from django import forms

class ContactForm(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Name'}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
    )
    subject = forms.ChoiceField(
        required=True,
        choices=[
            ('', 'Select Subject'),
            ('General Inquiry', 'General Inquiry'),
            ('Support', 'Support'),
            ('Feedback', 'Feedback'),
            ('Complaint', 'Complaint'),
        ],
        widget=forms.Select(attrs={'placeholder': 'Subject'}),
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'placeholder': 'Message', 'rows': 5}),
    )
    
        
    
        