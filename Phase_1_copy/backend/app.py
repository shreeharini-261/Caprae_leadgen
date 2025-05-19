### 1. First, modify your app.py to expose the webhook at the root level

from flask import Flask, has_request_context, g, request, jsonify
from models.lead_model import db
from routes.lead_routes import lead_bp
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from config.config import config
from flask_login import LoginManager, current_user
from models.user_model import User, db
from sqlalchemy import event, text
import stripe
import os


def create_app(config_class=config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Audit connection setup
    def set_app_user_on_connect(dbapi_connection, connection_record):
        try:
            # Only set if in a request context and user is authenticated
            if has_request_context() and current_user.is_authenticated:
                username = getattr(current_user, 'username', None)
                if username:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("SELECT set_app_user(%s);", (username, ))
                    cursor.close()
        except Exception:
            pass  # Ignore if user is not available (e.g., during migrations)

    @app.before_request
    def set_audit_user():
        if has_request_context() and current_user.is_authenticated:
            username = getattr(current_user, 'username', None)
            if username:
                # Use the current session, not a new engine connection
                db.session.execute(text("SELECT set_app_user(:username);"),
                                   {"username": username})

    # Register blueprints
    app.register_blueprint(main_bp)  # Register main routes first
    app.register_blueprint(auth_bp)  # Register auth routes
    app.register_blueprint(lead_bp)  # Then register other routes

    # Create database tables
    with app.app_context():
        db.create_all()
        event.listen(db.engine, "connect", set_app_user_on_connect)
        # Call the audit log setup from the model
        from models.audit_log_model import ensure_audit_log_infrastructure
        ensure_audit_log_infrastructure(db)

    # Add root level webhook route (this is the key fix)
    @app.route('/webhook', methods=['POST'])
    def stripe_webhook():
        print("Webhook received at root level!")
        payload = request.get_data()
        sig_header = request.headers.get('stripe-signature')

        try:
            stripe.api_key = app.config['STRIPE_SECRET_KEY']
            webhook_secret = app.config['STRIPE_WEBHOOK_SECRET']

            print(f"Processing webhook with secret: {webhook_secret[:4]}...")

            event = stripe.Webhook.construct_event(payload, sig_header,
                                                   webhook_secret)
            print(f"Webhook validated! Event type: {event['type']}")

            # Handle the checkout.session.completed event
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                user_id = session.get('client_reference_id')
                print(f"Payment successful for user {user_id}")

                # Process the subscription update
                handle_successful_payment(session)

            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                subscription_id = invoice.get('subscription')
                customer_id = invoice.get('customer')
                print(
                    f"Subscription payment succeeded for subscription {subscription_id}, customer {customer_id}"
                )

                # Process the subscription payment - can extend subscription
                # You might want to add logic here to extend subscription periods

        except ValueError as e:
            print(f"Webhook error: Invalid payload - {str(e)}")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError as e:
            print(f"Webhook error: Invalid signature - {str(e)}")
            return jsonify({'error': 'Invalid signature'}), 400
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return jsonify({'error': str(e)}), 400

        # Return a 200 response to acknowledge receipt of the event
        return jsonify({'status': 'success'})

    return app


# Helper function to process successful payments
def handle_successful_payment(session):
    try:
        user_id = session.get('client_reference_id')
        if not user_id:
            print("No user_id found in session")
            return

        user = User.query.get(int(user_id))
        if not user:
            print(f"User {user_id} not found")
            return

        # Get stripe API key from app config
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Get line items and extract price ID
        line_items = stripe.checkout.Session.list_line_items(session.id,
                                                             limit=1)
        if not line_items or not line_items.data:
            print("No line items found")
            return

        price_id = line_items.data[0].price.id

        # Map price_id to subscription tier
        price_to_tier = {
            config.STRIPE_PRICES['gold']: 'gold',
            config.STRIPE_PRICES['silver']: 'silver',
            config.STRIPE_PRICES['bronze']: 'bronze'
        }

        new_tier = price_to_tier.get(price_id)
        if not new_tier:
            print(f"Invalid price_id: {price_id}")
            return

        # Update user's subscription tier
        user.subscription_tier = new_tier
        db.session.commit()
        print(f"Successfully updated user {user_id} to tier {new_tier}")

    except Exception as e:
        print(f"Error handling payment: {str(e)}")
        db.session.rollback()


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
