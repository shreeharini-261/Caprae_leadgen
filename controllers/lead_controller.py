from flask import request, redirect, render_template, flash, url_for, jsonify
from models.lead_model import db, Lead
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import text

class LeadController:
    @staticmethod
    def get_all_leads(user=None):
        """Get leads based on user role and subscription"""
        query = Lead.query.order_by(Lead.updated_at.desc())
        
        # Admin users get full access
        if not user or user.is_admin():
            return query.all()
            
        # Get user's subscription tier, default to 'free'
        tier = getattr(user, 'subscription_tier', 'free')
        
        # Apply tier-based limitations
        if tier == 'free':
            return query.limit(10).all()  # Free users see only 10 leads
        elif tier == 'bronze':
            return query.limit(50).all()  # Bronze users see up to 50 leads
        elif tier == 'silver':
            return query.limit(100).all()  # Silver users see up to 100 leads
        else:  # gold tier
            return query.all()  # Gold users see all leads

    @staticmethod
    def get_lead_by_id(lead_id):
        """Get lead by ID"""
        # return Lead.query.filter_by(id=lead_id, deleted=False).first_or_404()
        return Lead.query.filter_by(id=lead_id).first_or_404()

    @staticmethod
    def get_leads_by_ids(lead_ids):
        """Get multiple leads by their IDs"""
        # return Lead.query.filter(Lead.id.in_(lead_ids), Lead.deleted==False).all()
        return Lead.query.filter(Lead.id.in_(lead_ids)).all()

    @staticmethod
    def create_lead(form_data):
        """Create new lead from form data"""
        # Create lead with basic information
        lead = Lead(
            # Basic contact info
            first_name=form_data.get('first_name', ''),
            last_name=form_data.get('last_name', ''),
            email=form_data.get('email', ''),
            phone=form_data.get('phone', ''),
            title=form_data.get('title', ''),

            # Company info
            company=form_data.get('company', ''),
            city=form_data.get('city', ''),
            state=form_data.get('state', ''),
            website=form_data.get('website', ''),
            industry=form_data.get('industry', ''),
            business_type=form_data.get('business_type', ''),

            # Other fields
            additional_notes=form_data.get('notes', '')
        )
        
        # Handle dynamic fields if provided
        if form_data.getlist('dynamic_field_name[]') and form_data.getlist('dynamic_field_value[]'):
            field_names = form_data.getlist('dynamic_field_name[]')
            field_values = form_data.getlist('dynamic_field_value[]')
            
            for i in range(len(field_names)):
                if field_names[i] and field_values[i]:
                    # Set attribute if it exists on Lead model
                    field_name = field_names[i]
                    if hasattr(lead, field_name):
                        setattr(lead, field_name, field_values[i])
        
        try:
            db.session.add(lead)
            db.session.commit()
            return True, "Lead added successfully!"
        except IntegrityError as e:
            db.session.rollback()
            if "lead_email_key" in str(e):
                return False, f"Error: Email address '{lead.email}' is already in use. Please use a different email."
            elif "lead_phone_key" in str(e):
                return False, f"Error: Phone number '{lead.phone}' is already in use. Please use a different phone number."
            else:
                return False, f"Error adding lead: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error adding lead: {str(e)}"

    @staticmethod
    def update_lead(lead_id, form_data):
        """Update existing lead"""
        lead = Lead.query.get_or_404(lead_id)
        
        # Store original email and phone for comparison
        original_email = lead.email
        original_phone = lead.phone
        
        lead.first_name = form_data.get('first_name', '')
        lead.last_name = form_data.get('last_name', '')
        lead.email = form_data.get('email', '')
        lead.phone = form_data.get('phone', '')
        lead.company = form_data.get('company', '')
        lead.industry = form_data.get('industry', '')
        lead.city = form_data.get('city', '')
        lead.state = form_data.get('state', '')
        lead.website = form_data.get('website', '')
        lead.business_type = form_data.get('business_type', '')
        lead.status = form_data.get('status', lead.status)
        
        # Handle dynamic fields if provided
        if form_data.getlist('dynamic_field_name[]') and form_data.getlist('dynamic_field_value[]'):
            field_names = form_data.getlist('dynamic_field_name[]')
            field_values = form_data.getlist('dynamic_field_value[]')
            
            for i in range(len(field_names)):
                if field_names[i] and field_values[i]:
                    # Set attribute if it exists on Lead model
                    field_name = field_names[i]
                    if hasattr(lead, field_name):
                        setattr(lead, field_name, field_values[i])
        
        try:
            # Only commit if email or phone has changed
            if lead.email != original_email or lead.phone != original_phone:
                db.session.commit()
            else:
                # If no change to unique fields, this should be safe
                db.session.commit() 
            return True, "Lead updated successfully!"
        except IntegrityError as e:
            db.session.rollback()
            if "lead_email_key" in str(e):
                return False, f"Error: Email address '{lead.email}' is already used by another lead. Please use a different email."
            elif "lead_phone_key" in str(e):
                return False, f"Error: Phone number '{lead.phone}' is already used by another lead. Please use a different phone number."
            else:
                return False, f"Error updating lead: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating lead: {str(e)}"

    @staticmethod
    def delete_lead(lead_id, current_user=None):
        """Soft delete lead by ID"""
        lead = Lead.query.get_or_404(lead_id)

        try:
            # Set current user for audit log if provided
            if current_user:
                user_name = current_user.username if hasattr(current_user, 'username') else str(current_user)
                db.session.execute(text("SELECT set_app_user(:username)"), {'username': user_name})
                
            # Instead of deleting, mark as deleted
            lead.deleted = True
            lead.deleted_at = datetime.utcnow()
            db.session.commit()
            return True, "Lead deleted successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting lead: {str(e)}"

    @staticmethod
    def delete_multiple_leads(lead_ids, current_user=None):
        """Soft delete multiple leads by their IDs"""
        if not lead_ids:
            return False, "No leads selected for deletion."
            
        try:
            # Set current user for audit log if provided
            if current_user:
                user_name = current_user.username if hasattr(current_user, 'username') else str(current_user)
                db.session.execute(text("SELECT set_app_user(:username)"), {'username': user_name})
                
            # Get all leads to be deleted
            leads = Lead.query.filter(Lead.id.in_(lead_ids)).all()
            
            if not leads:
                return False, "No leads found with the specified IDs."
                
            # Mark all leads as deleted
            now = datetime.utcnow()
            for lead in leads:
                lead.deleted = True
                lead.deleted_at = now
                
            db.session.commit()
            return True, f"{len(leads)} leads deleted successfully!"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting leads: {str(e)}"

    @staticmethod
    def get_leads_json():
        """Get all leads as JSON for API"""
        leads = Lead.query.filter_by(deleted=False).all()
        return [lead.to_dict() for lead in leads]

    @staticmethod
    def add_or_update_lead_by_match(lead_data):
        """Add a new lead or update existing lead by matching email or phone"""
        try:
            existing_lead = Lead.query.filter(
                (Lead.email == lead_data['email']) | (Lead.phone == lead_data['phone'])
            ).first()

            if existing_lead:
                for key, value in lead_data.items():
                    if hasattr(existing_lead, key):
                        setattr(existing_lead, key, value)
                db.session.commit()
                return True, ""
            else:
                lead = Lead(**lead_data)
                db.session.add(lead)
                db.session.commit()
                return True, ""
        except IntegrityError as e:
            db.session.rollback()
            # Use generic error message instead of specific ones
            return False, "Duplicate data detected"
        except Exception as e:
            db.session.rollback()
            return False, f"Error adding/updating lead: {str(e)}"