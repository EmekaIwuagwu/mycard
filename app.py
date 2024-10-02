import os
from flask import Flask, render_template, request, redirect
import stripe

app = Flask(__name__)

# Hardcoded Stripe secret and public keys
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_live_51Q44BMFHz9inXqLwPH9i0W0OTZbgV2Qwdp1B4HlhF6vOiYuA7EsrBadxzEoebbw73FlDMCN580qsoLSDExSbQSVL00kJG6JQvY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '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')

stripe.api_key = STRIPE_SECRET_KEY

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/payment', methods=['POST'])
def payment_redirect():
    amount = request.form['amount']  # Get amount from form submission
    return render_template('payment.html', amount=amount, public_key=STRIPE_PUBLIC_KEY)

@app.route('/charge', methods=['POST'])
def charge():
    amount = int(float(request.form['amount']) * 100)  # Convert to cents
    token = request.form['stripeToken']
    
    # Capture additional user information
    name = request.form['name']
    address = request.form['address']
    zip_code = request.form['zip']
    country = request.form['country']

    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency='usd',
            description='Payment by ' + name + ' for amount $' + '{:.2f}'.format(amount / 100.0),
            source=token,
            shipping={
                'name': name,
                'address': {
                    'line1': address,
                    'postal_code': zip_code,
                    'country': country
                },
            },
        )
        return redirect('/success?ref={}'.format(charge.id))  # Pass transaction reference to success page

    except stripe.error.StripeError as e:
        return 'Error: {}'.format(str(e))


@app.route('/success')
def success():
    return render_template('success.html')  # Create a success.html template

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=False)  # Bind to 0.0.0.0 for external access
