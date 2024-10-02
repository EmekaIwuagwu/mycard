import os
from flask import Flask, render_template, request, redirect
import stripe

app = Flask(__name__)

# Hardcoded Stripe secret and public keys
STRIPE_PUBLIC_KEY = 'pk_test_51Q44BMFHz9inXqLwQhDWvdMJFrWWpiGyRxlusfoDkT9bAIBy1Chsdw7AJflhOWmxF5bp6CXyRscKUTveS1m5tOGM00uKJKZALZ'
STRIPE_SECRET_KEY = 'sk_test_51Q44BMFHz9inXqLwaRmVsewpCyTkD233i79dkIchcfLuSQLoCmZqMpdLhikiZOSnRc57SPfWLI2BtVG1A6BSPAbU00vfIVLRph'

# Set the Stripe secret key
stripe.api_key = STRIPE_SECRET_KEY

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/payment', methods=['POST'])
def payment_redirect():
    amount = request.form['amount']  # Get amount from form submission
    return render_template('payment_method_selection.html', amount=amount)

@app.route('/payment_method', methods=['POST'])
def payment_method():
    amount = request.form['amount']
    payment_method = request.form['payment_method']
    
    if payment_method == 'credit_card':
        return render_template('payment.html', amount=amount, public_key=STRIPE_PUBLIC_KEY, method='credit_card')
    elif payment_method == 'ach':
        return render_template('ach_payment.html', amount=amount)

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

@app.route('/ach_charge', methods=['POST'])
def ach_charge():
    amount = int(float(request.form['amount']) * 100)  # Convert to cents
    account_number = request.form['account_number']
    routing_number = request.form['routing_number']

    try:
        # Create a bank account token using Stripe's API
        bank_account_token = stripe.Token.create({
            'bank_account': {
                'account_number': account_number,
                'routing_number': routing_number,
                'country': 'US',
                'account_holder_name': request.form['name'],
                'account_holder_type': 'individual',  # or 'company'
            },
        })

        # Create a PaymentIntent for the ACH payment
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            payment_method=bank_account_token.id,
            confirmation_method='automatic',  # Automatically confirm the payment
            confirm=True,  # Automatically confirm the payment
            description='ACH Payment for amount $' + '{:.2f}'.format(amount / 100.0),
        )
        
        return redirect('/success?ref={}'.format(payment_intent.id))

    except stripe.error.StripeError as e:
        return 'Error: {}'.format(str(e))


@app.route('/success')
def success():
    return render_template('success.html')  # Create a success.html template

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug=True for development
