from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Company Information
    company = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    website = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    revenue = db.Column(db.String(100))
    product_service_category = db.Column(db.Text)
    business_type = db.Column(db.String(100))  # B2B, B2B2C
    associated_members = db.Column(db.Text)
    employees_range = db.Column(db.String(100))
    rev_source = db.Column(db.String(100))
    year_founded = db.Column(db.String(20))
    
    # Contact Information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(30), unique=True)
    title = db.Column(db.String(100))
    
    # Owner Information
    owner_linkedin = db.Column(db.String(255))
    owner_age = db.Column(db.String(20))
    
    # Notes and Scoring
    additional_notes = db.Column(db.Text)
    score = db.Column(db.String(20))
    reasoning = db.Column(db.Text)  # Reasoning for r/y/g
    
    # Email Customization
    email_customization_1 = db.Column(db.Text)
    subject_line_1 = db.Column(db.String(255))
    email_customization_2 = db.Column(db.Text)
    subject_line_2 = db.Column(db.String(255))
    
    # LinkedIn Customization
    linkedin_customization_1 = db.Column(db.Text)
    linkedin_customization_2 = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='new', nullable=False)


    # Only truncate these fields if needed
    # FIELD_MAX_LENGTHS = {
    #     'product_service_category': 2000,
    #     'business_type': 100,
    # }

    # @classmethod
    # def truncate_fields(cls, data):
    #     for field, max_len in cls.FIELD_MAX_LENGTHS.items():
    #         if field in data and isinstance(data[field], str):
    #             data[field] = data[field][:max_len]
    #     return data
    
    # @property
    # def full_name(self):
    #     """Return the full name of the lead"""
    #     return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f'<Lead {self.company}: {self.first_name} {self.last_name}>'
    
    # Helper method to convert to dictionary
    def to_dict(self):
        """Convert Lead object to dictionary for API response"""
        return {
            'id': self.id,
            'company': self.company,
            'first_name': self.first_name,
            'last_name': self.last_name,
            # 'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'title': self.title,
            'city': self.city,
            'state': self.state,
            'website': self.website,
            'linkedin_url': self.linkedin_url,
            'industry': self.industry,
            'revenue': self.revenue,
            'product_service_category': self.product_service_category,
            'business_type': self.business_type,
            'associated_members': self.associated_members,
            'employees_range': self.employees_range,
            'rev_source': self.rev_source,
            'year_founded': self.year_founded,
            'owner_linkedin': self.owner_linkedin,
            'owner_age': self.owner_age,
            'additional_notes': self.additional_notes,
            'score': self.score,
            'email_customization_1': self.email_customization_1,
            'subject_line_1': self.subject_line_1,
            'email_customization_2': self.email_customization_2,
            'subject_line_2': self.subject_line_2,
            'linkedin_customization_1': self.linkedin_customization_1,
            'linkedin_customization_2': self.linkedin_customization_2,
            'reasoning': self.reasoning,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted': self.deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        } 