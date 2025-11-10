from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, SubmitField
from wtforms.validators import Optional, Length

class ProfileForm(FlaskForm):
    first_name = StringField("First name", validators=[Optional(), Length(max=100)])
    surname = StringField("Surname", validators=[Optional(), Length(max=100)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    company_name = StringField("Company name", validators=[Optional(), Length(max=150)])
    position_in_company = StringField("Position", validators=[Optional(), Length(max=50)])
    company_website = StringField("Company website", validators=[Optional(), Length(max=255)])
    company_address = StringField("Company address", validators=[Optional(), Length(max=300)])
    aum = FloatField("AUM", validators=[Optional()])

    # New preferences as StringFields (as requested)
    preferred_asset_classes = StringField("Preferred Project Types", validators=[Optional(), Length(max=300)])
    location_type_preference = StringField("Location type preference", validators=[Optional(), Length(max=200)])
    target_min_irr = StringField("Target minimum IRR (%)", validators=[Optional(), Length(max=20)])

    # Ticket min/max (also strings; change to FloatField if you want numeric validation)
    ticket_min = StringField("Ticket min", validators=[Optional(), Length(max=50)])
    ticket_max = StringField("Ticket max", validators=[Optional(), Length(max=50)])

    # Email updates toggle
    email_updates = BooleanField("Email me updates and deal digests")

    submit = SubmitField("Save profile")
