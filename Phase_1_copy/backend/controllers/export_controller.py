import pandas as pd
from io import BytesIO
import datetime
from models.lead_model import Lead
import openpyxl  # Required for Excel export

class ExportController:
    @staticmethod
    def export_leads_to_file(lead_ids=None, file_format='csv', filter_params=None):
        """
        Export leads to CSV or Excel, either by specific IDs or filtered by parameters
        Args:
            lead_ids (list, optional): List of lead IDs to export
            file_format (str): Format to export ('csv' or 'excel')
            filter_params (dict, optional): Dictionary of filter parameters
        Returns:
            tuple: (BytesIO object, filename, mimetype) or (None, None, None) if no leads found
        """
        # Query to get leads
        query = Lead.query
        
        # Apply filters if provided
        if filter_params:
            if filter_params.get('company'):
                query = query.filter(Lead.company == filter_params.get('company'))
            if filter_params.get('location'):
                location_parts = filter_params.get('location').split(', ', 1)
                if len(location_parts) == 2:
                    city, state = location_parts
                    query = query.filter(Lead.city == city, Lead.state == state)
                else:
                    query = query.filter((Lead.city == location_parts[0]) | (Lead.state == location_parts[0]))
            if filter_params.get('role'):
                query = query.filter(Lead.title == filter_params.get('role'))
            if filter_params.get('status'):
                query = query.filter(Lead.status == filter_params.get('status'))
            if filter_params.get('revenue'):
                revenue_value = filter_params.get('revenue')
                # Handle revenue filtering by comparing revenue values
                try:
                    # Parse revenue value (handle $XM format)
                    revenue_threshold = ExportController.parse_revenue_value(revenue_value)
                    if revenue_threshold is not None:
                        # Get all leads with non-null revenue
                        leads_with_revenue = []
                        revenue_query = query.filter(Lead.revenue.isnot(None)).all()
                        
                        for lead in revenue_query:
                            # Parse each lead's revenue and compare with threshold
                            lead_revenue = ExportController.parse_revenue_value(lead.revenue)
                            if lead_revenue is not None and lead_revenue >= revenue_threshold:
                                leads_with_revenue.append(lead.id)
                        
                        # Update query to only include leads with revenue >= threshold
                        if leads_with_revenue:
                            query = query.filter(Lead.id.in_(leads_with_revenue))
                        else:
                            # No leads match the criteria
                            return None, None, None
                except:
                    # If parsing fails, just look for exact match
                    query = query.filter(Lead.revenue == revenue_value)
            if filter_params.get('search'):
                search_term = f"%{filter_params.get('search')}%"
                query = query.filter(
                    (Lead.company.ilike(search_term)) |
                    (Lead.first_name.ilike(search_term)) |
                    (Lead.last_name.ilike(search_term)) |
                    (Lead.email.ilike(search_term)) |
                    (Lead.phone.ilike(search_term)) |
                    (Lead.title.ilike(search_term)) |
                    (Lead.city.ilike(search_term)) |
                    (Lead.state.ilike(search_term))
                )
        
        # Apply lead_ids filter if provided
        if lead_ids:
            query = query.filter(Lead.id.in_(lead_ids))
        
        # Execute query
        leads = query.all()
        
        if not leads:
            return None, None, None

        # Convert leads to list of dictionaries
        data = []
        for lead in leads:
            lead_dict = {
                'Company': lead.company,
                'First Name': lead.first_name,
                'Last Name': lead.last_name,
                'Email': lead.email,
                'Phone': lead.phone,
                'Title': lead.title,
                'City': lead.city,
                'State': lead.state,
                'Website': lead.website,
                'LinkedIn URL': lead.linkedin_url,
                'Industry': lead.industry,
                'Revenue': lead.revenue,
                'Product/Service Category': lead.product_service_category,
                'Business Type': lead.business_type,
                'Employees Range': lead.employees_range,
                'Year Founded': lead.year_founded,
                'Owner LinkedIn': lead.owner_linkedin,
                'Owner Age': lead.owner_age,
                # 'Score': lead.score,
                'Status': lead.status,
                # 'Reasoning': lead.reasoning,
                'Notes': lead.additional_notes,
                # 'Subject Line 1': lead.subject_line_1,
                # 'Email Content 1': lead.email_customization_1,
                # 'Subject Line 2': lead.subject_line_2,
                # 'Email Content 2': lead.email_customization_2,
                # 'LinkedIn Message 1': lead.linkedin_customization_1,
                # 'LinkedIn Message 2': lead.linkedin_customization_2,
                'Created At': lead.created_at,
                'Updated At': lead.updated_at
            }
            data.append(lead_dict)

        # Create DataFrame
        df = pd.DataFrame(data)

        # Create BytesIO object
        output = BytesIO()
        
        # Create filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if file_format.lower() == 'excel':
            # Export to Excel
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads')
            filename = f'exported_leads_{timestamp}.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            # Export to CSV
            df.to_csv(output, index=False, encoding='utf-8-sig')
            filename = f'exported_leads_{timestamp}.csv'
            mimetype = 'text/csv'

        output.seek(0)
        return output, filename, mimetype 

    @staticmethod
    def parse_revenue_value(revenue_str):
        """
        Parse revenue values in format like $5M, $1.5M, etc.
        Returns None if parsing fails
        """
        if not revenue_str or revenue_str == '-':
            return None
        
        # Handle "nan" value
        if revenue_str.lower() == 'nan':
            return 0
        
        # Remove $ and any other non-numeric characters except . and M
        clean_str = revenue_str.replace('$', '').strip()
        
        try:
            if clean_str.endswith('M') or clean_str.endswith('m'):
                # Convert $XM format to a number (millions)
                return float(clean_str[:-1])
            elif clean_str.endswith('K') or clean_str.endswith('k'):
                # Convert $XK format to a number (thousands)
                return float(clean_str[:-1]) / 1000  # Convert to millions
            else:
                # Try to parse as a direct number
                return float(clean_str)
        except ValueError:
            return None 