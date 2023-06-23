import streamlit as st
import stripe
from deta import Deta
import base64
import sendgrid
from sendgrid.helpers.mail import Mail
import config

detakey = config.deta_key
deta = Deta(detakey)
db = deta.Base("ticketscrappertest1")
stripe.api_key = config.stripe_key
sg = sendgrid.SendGridAPIClient(api_key=config.sendgrid_key)

def retrieve_customer_subscription(email):
    customers = stripe.Customer.list(email=email)
    if customers.data:
        customer_id = customers.data[0].id
        subscriptions = stripe.Subscription.list(customer=customer_id)
        if subscriptions.data:
            subscription_id = subscriptions.data[0].id
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
    return None

def cancel_membership(email):
    
    # Replace with the user's email address
    subscription = retrieve_customer_subscription(email)

    if subscription:
        try:
            subscription.cancel_at_period_end = True
            subscription.save()
            st.success("Membership cancellation scheduled.")
        except Exception as e:
            st.error(f"Failed to schedule membership cancellation. Error: {str(e)}")
    else:
        st.error("Subscription not found for the customer.")

def check_value_exists(column_name, value):
    # Query the database for rows with the specified value in the column
    query = db.fetch({column_name : value})
    
    # Check if any rows are returned
    if len(query.items) > 0:
        return True #value does exist
    else:
        return False #value does not exist

def find_dictionary_index(dictionaries, email):
    for index, dictionary in enumerate(dictionaries):
        if dictionary.get('email') == email:
            return index
    return -1

# Extract the encoded email and password from the URL parameters
encoded_email = st.experimental_get_query_params().get("email", [""])[0]

# Decode the email and password using Base64
email = base64.b64decode(encoded_email).decode()

if check_value_exists("email", email) == True:

    # Get the specific user information from the database
    content = db.fetch().items
    index = find_dictionary_index(content, email)
    key_db = content[index]['key']
    user_data = db.get(key_db)

    #Obligated to leave an inquiry message
    st.title('Cancel Membership')
    email_content = st.text_area('Feedback', height=200, max_chars=750, )
    

    # Button to send email
    
    if st.button('Send Email'):
        if not email_content:
            st.warning('Please write a feedback')

        else:

            # Create a SendGrid message
            message = Mail(
                from_email = 'laurent.dderome@gmail.com',  #ANY ADDRESS USED TO SEND EMAILS
                to_emails = 'laurentderome9@gmail.com', #MY EMAIL TO RECEIVE INQUIRY FROM CUSTOMERS
                subject=f'Streamlit Inquiry Email : Cancel Membership',
                plain_text_content=f"""*Content*: {email_content} 
    --------------------
    Inquiry made by EMAIL: ({user_data['email']}), USERNAME: ({user_data['username']})""")
            

            try:
                # Send the email using SendGrid API
                response = sg.send(message)

                if response.status_code == 202:
                    cancel_membership(user_data['email'])
                else:
                    st.error('Error, please contact the support team')
            except Exception as e:
                st.error(f'An error occurred: {str(e)}')

else:
    st.error("The email wasn't found in the database")
