from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify, send_file
from controllers.lead_controller import LeadController
from controllers.upload_controller import UploadController
from controllers.export_controller import ExportController
from controllers.dashboard_controller import DashboardController
from models.lead_model import db, Lead
from flask_login import login_required, current_user
from utils.decorators import role_required
import csv
from io import StringIO, BytesIO
import datetime
import pandas as pd
import io

# Create blueprint
lead_bp = Blueprint('lead', __name__)

@lead_bp.route('/')
def index():
    """Display dashboard as home page"""
    stats = DashboardController.get_dashboard_stats()
    return render_template('dashboard.html', **stats)

@lead_bp.route('/form')
@login_required
def form():
    """Display form to add new lead"""
    return render_template('form.html')

@lead_bp.route('/submit', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def submit():
    """Submit new lead - Admin and Developer only"""
    success, message = LeadController.create_lead(request.form)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/upload_page')
@login_required
def upload_page():
    """Display CSV upload page"""
    return render_template('upload.html')

@lead_bp.route('/upload', methods=['POST'])
@login_required
def upload_csv():
    """Handle CSV file upload"""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('lead.upload_page'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('lead.upload_page'))

    name_col = request.form.get('name_column')
    email_col = request.form.get('email_column')
    phone_col = request.form.get('phone_column')
    first_name_col = request.form.get('first_name_column')
    last_name_col = request.form.get('last_name_column')

    # Collect dynamic field mappings
    dynamic_field_names = request.form.getlist('dynamic_field_name[]')
    dynamic_field_values = request.form.getlist('dynamic_field_value[]')
    dynamic_fields = {name: value for name, value in zip(dynamic_field_names, dynamic_field_values) if name and value}

    try:
        added, skipped_duplicates, errors = UploadController.process_csv_file(
            file,
            name_col,
            email_col,
            phone_col,
            dynamic_fields,
            first_name_col=first_name_col,
            last_name_col=last_name_col
        )
        db.session.commit()
        flash(f'Upload Complete! Added: {added}, Skipped: {skipped_duplicates}, Errors: {errors}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during upload: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/view_leads')
@login_required
def view_leads():
    """View all leads - All roles can access with limitations"""
    leads = LeadController.get_all_leads(current_user)
    
    # Get unique values for filters
    companies = sorted(set(lead.company for lead in leads if lead.company))
    locations = sorted(set(f"{lead.city}, {lead.state}" if lead.city and lead.state else (lead.city or lead.state) for lead in leads if (lead.city or lead.state)))
    roles = sorted(set(lead.title for lead in leads if lead.title))
    scores = sorted(set(lead.score for lead in leads if lead.score))
    statuses = sorted(set(lead.status for lead in leads if lead.status))
    
    # Get additional filter options
    industries = sorted(set(lead.industry for lead in leads if lead.industry))
    business_types = sorted(set(lead.business_type for lead in leads if lead.business_type))
    states = sorted(set(lead.state for lead in leads if lead.state))
    employee_sizes = sorted(set(lead.employees_range for lead in leads if lead.employees_range))
    revenue_ranges = sorted(set(lead.revenue for lead in leads if lead.revenue))
    
    return render_template('leads.html', 
                         leads=leads,
                         companies=companies,
                         locations=locations,
                         roles=roles,
                         scores=scores,
                         statuses=statuses,
                         industries=industries,
                         business_types=business_types,
                         states=states,
                         employee_sizes=employee_sizes,
                         revenue_ranges=revenue_ranges)

@lead_bp.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'developer')
def edit_lead(lead_id):
    """Edit lead - Admin and Developer only"""
    if request.method == 'POST':
        success, message = LeadController.update_lead(lead_id, request.form)

        if success:
            flash(message, 'success')
            return redirect(url_for('lead.view_leads'))
        else:
            flash(message, 'danger')

    lead = LeadController.get_lead_by_id(lead_id)
    return render_template('edit_lead.html', lead=lead)

@lead_bp.route('/update_status/<int:lead_id>', methods=['POST'])
@login_required
def update_status(lead_id):
    """Update lead status - All roles can update status"""
    try:
        lead = Lead.query.get_or_404(lead_id)
        new_status = request.form.get('status')
        if new_status:
            lead.status = new_status
            db.session.commit()
            flash('Status updated successfully', 'success')
        else:
            flash('No status provided', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/delete/<int:lead_id>')
@login_required
@role_required('admin', 'developer')
def delete_lead(lead_id):
    """Soft delete lead - Admin and Developer only"""
    try:
        # Use the controller method which now implements soft delete
        # Pass current_user for audit logging
        success, message = LeadController.delete_lead(lead_id, current_user=current_user)
        if success:
            flash('Lead deleted successfully', 'success')
        else:
            flash(message, 'danger')
    except Exception as e:
        flash(f'Error deleting lead: {str(e)}', 'danger')

    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/delete_multiple_leads', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def delete_multiple_leads():
    """Soft delete multiple leads - Admin and Developer only"""
    selected_leads = request.form.getlist('selected_leads[]')
    
    if not selected_leads:
        flash('No leads selected for deletion', 'danger')
        return redirect(url_for('lead.view_leads'))
    
    # Convert string IDs to integers
    lead_ids = [int(id) for id in selected_leads if id.isdigit()]
    
    # Pass current_user for audit logging
    success, message = LeadController.delete_multiple_leads(lead_ids, current_user=current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('lead.view_leads'))

@lead_bp.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    """API endpoint to get all leads - All roles can access"""
    leads = LeadController.get_leads_json()
    return jsonify(leads)

@lead_bp.route('/api/leads', methods=['POST'])
@login_required
@role_required('admin', 'developer')
def create_lead():
    """Create a new lead via API - Admin and Developer only"""
    data = request.json
    lead = Lead(**data)
    
    try:
        db.session.add(lead)
        db.session.commit()
        return jsonify({"message": "Lead created successfully", "lead": lead.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<int:lead_id>', methods=['PUT'])
@login_required
@role_required('admin', 'developer')
def update_lead_api(lead_id):
    """Update a lead via API - Admin and Developer only"""
    lead = Lead.query.get_or_404(lead_id)
    data = request.json
    
    try:
        for key, value in data.items():
            setattr(lead, key, value)
        db.session.commit()
        return jsonify({"message": "Lead updated successfully", "lead": lead.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/api/leads/<int:lead_id>/status', methods=['PUT'])
@login_required
def update_status_api(lead_id):
    """Update a lead's status via API - All roles can update status"""
    lead = Lead.query.get_or_404(lead_id)
    data = request.json
    
    if 'status' not in data:
        return jsonify({"error": "Status field is required"}), 400
    
    try:
        lead.status = data['status']
        db.session.commit()
        return jsonify({"message": "Status updated successfully", "lead": lead.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@lead_bp.route('/export_leads', methods=['POST'])
@login_required
def export_leads():
    """Export selected leads to CSV or Excel - All roles can export"""
    # Allow admins to export without restrictions
    if current_user.role == 'admin':
        try:
            selected_leads = request.form.getlist('selected_leads[]')
            file_format = request.form.get('file_format', 'csv')
            export_type = request.form.get('export_type', 'selected')
            
            # Get filter parameters if exporting filtered data
            filter_params = None
            if export_type == 'filtered':
                filter_params = {k: v for k, v in request.form.items() if v and k in ['company', 'location', 'role', 'status', 'revenue', 'search']}
            
            if export_type == 'selected' and not selected_leads:
                flash('Please select at least one lead to export', 'danger')
                return redirect(url_for('lead.view_leads'))
            
            output, filename, mimetype = ExportController.export_leads_to_file(
                selected_leads if export_type == 'selected' else None,
                file_format,
                filter_params if export_type == 'filtered' else None
            )
            
            if output is None:
                flash('No leads found to export', 'danger')
                return redirect(url_for('lead.view_leads'))
                
            return send_file(
                output,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            flash(f'Error exporting leads: {str(e)}', 'danger')
            return redirect(url_for('lead.view_leads'))
            
    # Show subscription modal for free users
    if current_user.subscription_tier == 'free':
        return render_template('leads.html', 
                             show_subscription_modal=True, 
                             subscription_message='Export feature requires a paid plan',
                             leads=LeadController.get_all_leads(current_user))
    selected_leads = request.form.getlist('selected_leads[]')
    file_format = request.form.get('file_format', 'csv')
    export_type = request.form.get('export_type', 'selected')
    
    # Get filter parameters if exporting filtered data
    filter_params = None
    if export_type == 'filtered':
        filter_params = {
            'company': request.form.get('company', ''),
            'location': request.form.get('location', ''),
            'role': request.form.get('role', ''),
            'status': request.form.get('status', ''),
            'revenue': request.form.get('revenue', ''),
            'search': request.form.get('search', '')
        }
        # Remove empty filters
        filter_params = {k: v for k, v in filter_params.items() if v}
    
    # Check if we're exporting selected leads and if any are selected
    if export_type == 'selected' and not selected_leads:
        flash('Please select at least one lead to export', 'danger')
        return redirect(url_for('lead.view_leads'))
    
    try:
        # Pass either lead_ids or filter_params based on export type
        if export_type == 'selected':
            output, filename, mimetype = ExportController.export_leads_to_file(selected_leads, file_format)
        else:  # filtered
            output, filename, mimetype = ExportController.export_leads_to_file(None, file_format, filter_params)
        
        if output is None:
            flash('No leads found to export', 'danger')
            return redirect(url_for('lead.view_leads'))
            
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error exporting leads: {str(e)}', 'danger')
        return redirect(url_for('lead.view_leads'))

@lead_bp.route('/dashboard')
@login_required
def dashboard():
    """Display dashboard - All roles can access"""
    stats = DashboardController.get_dashboard_stats()
    return render_template('dashboard.html', **stats)

@lead_bp.route('/api/upload_leads', methods=['POST'])
@login_required
def api_upload_leads():
    """API endpoint"""
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return jsonify({"status": "error", "message": "Invalid data format. Expected a list of leads"}), 400
        
        # Initial validation - check required fields only once
        required_fields = ['email', 'phone', 'website','company']
        valid_leads = []
        invalid_indices = []
        
        # Pre-validate all leads at once
        for i, lead in enumerate(data):
            if all(field in lead for field in required_fields):
                # Clean email and phone
                lead['email'] = UploadController.clean_email(lead['email'])
                lead['phone'] = UploadController.clean_phone(lead['phone'])
                lead['website'] = UploadController.clean_website(lead['website'])
                lead['company'] = UploadController.clean_company(lead['company'])
                
                # Quick validation
                if UploadController.is_valid_email(lead['email']) and UploadController.is_valid_phone(lead['phone']) and UploadController.is_valid_website(lead['website']) and UploadController.is_valid_company(lead['company']):
                    # Truncate fields to match database limitations
                    lead = Lead.truncate_fields(lead)
                    valid_leads.append(lead)
                else:
                    invalid_indices.append(i)
            else:
                invalid_indices.append(i)
                
        # Process all valid leads in bulk
        added = 0
        skipped = 0
        
        # Get all existing emails, phones, and websites in one query to check duplicates efficiently
        existing_leads = db.session.query(Lead.email, Lead.phone, Lead.website, Lead.company).all()
        existing_emails = {lead.email for lead in existing_leads}
        existing_phones = {lead.phone for lead in existing_leads}
        existing_websites = {lead.website for lead in existing_leads}
        existing_companies = {lead.company for lead in existing_leads}
        
        # Prepare lists for bulk operations
        new_leads = []
        
        for lead_data in valid_leads:
            # Check if it's a duplicate
            if lead_data['email'] in existing_emails or lead_data['phone'] in existing_phones or lead_data['website'] in existing_websites or lead_data['company'] in existing_companies:
                skipped += 1
                continue
                
            # Add to new leads list for bulk insert
            new_lead = Lead(**lead_data)
            new_leads.append(new_lead)
            
            # Update tracking sets to prevent duplicates within the same batch
            existing_emails.add(lead_data['email'])
            existing_phones.add(lead_data['phone'])
            existing_websites.add(lead_data['website'])
            existing_companies.add(lead_data['company'])
            
        # Bulk insert new leads
        if new_leads:
            db.session.bulk_save_objects(new_leads)
            db.session.commit()
            added = len(new_leads)
        
        # Calculate statistics
        errors = len(invalid_indices)
        
        return jsonify({
            "status": "success",
            "message": f"Upload Complete! Added: {added}, Skipped: {skipped}, Errors: {errors}",
            "stats": {
                "added": added,
                "skipped_duplicates": skipped,
                "errors": errors,
                "invalid_indices": invalid_indices[:10] if invalid_indices else []
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Error during upload: {str(e)}"
        }), 500

@lead_bp.route('/api/leads/<int:lead_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'developer')
def delete_lead_api(lead_id):
    """Soft delete a lead via API - Admin and Developer only"""
    try:
        # Use the controller method which implements soft delete
        success, message = LeadController.delete_lead(lead_id, current_user=current_user)
        if success:
            return jsonify({"message": "Lead successfully deleted"})
        else:
            return jsonify({"error": message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500