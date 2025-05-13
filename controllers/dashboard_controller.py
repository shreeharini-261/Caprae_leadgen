from models.lead_model import Lead, db
from sqlalchemy import func, cast, Float, and_, not_
from datetime import datetime, timedelta

class DashboardController:
    @staticmethod
    def get_dashboard_stats():
        """Get statistics for the dashboard"""
        try:
            # Get total leads (handle None case)
            total_leads = Lead.query.count() or 0
            
            # Get today's imported leads
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            todays_leads = Lead.query.filter(
                Lead.created_at.between(today_start, today_end)
            ).count() or 0
            
            # Get high scoring leads (handle null scores, NaN strings, and invalid values)
            high_scoring_leads = Lead.query.filter(
                and_(
                    Lead.score.isnot(None),  # Filter out null scores
                    Lead.score != 'NaN',     # Filter out 'NaN' string values
                    Lead.score != '',        # Filter out empty strings
                    cast(Lead.score, Float) > 0.7
                )
            ).count() or 0
            
            # Calculate average score with proper error handling
            try:
                avg_score_result = db.session.query(
                    func.avg(cast(Lead.score, Float))
                ).filter(
                    Lead.score.isnot(None),  # Filter out null scores
                    Lead.score != 'NaN',     # Filter out 'NaN' string values
                    Lead.score != '',        # Filter out empty strings
                    cast(Lead.score, Float).between(0, 1)  # Only consider valid scores between 0 and 1
                ).scalar()
                
                # Handle None, NaN, or invalid values
                if avg_score_result is not None and str(avg_score_result) != 'nan':
                    avg_score = round(float(avg_score_result) * 100, 1)
                else:
                    avg_score = 0
            except (ValueError, TypeError):
                avg_score = 0
            
            return {
                'total_leads': total_leads,
                'todays_leads': todays_leads,
                'high_scoring_leads': high_scoring_leads,
                'avg_score': avg_score
            }
        except Exception as e:
            print(f"Error getting dashboard stats: {str(e)}")
            return {
                'total_leads': 0,
                'todays_leads': 0,
                'high_scoring_leads': 0,
                'avg_score': 0
            } 