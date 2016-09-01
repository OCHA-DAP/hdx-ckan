import logging
log = logging.getLogger(__name__)


_SUBJECT_MEMBERSHIP_REQUEST = '''{user_fullname} sent a request to join your organisation on HDX'''
_MESSAGE_MEMBERSHIP_REQUEST = \
    '''
    <br/><br/>You are receiving this message because you are an administrator of the {org_title} organisation on HDX
    and a user called {user_fullname} whose email address is {user_email} has requested to join your organisation
    on HDX. The user included the following message with his/her request: <br/>{user_message} <br/><br/>
    If you know this user and would like to add him/her to your organisation, please log on to HDX and click on the
    ADD MEMBER link for your organisation at {org_add_member_url} .
    Enter \'{user_username}\' in the username box in \'Add / invite colleagues to this organisation\' section and
    assign one of the following roles to the user: <br/>
    - Admin: The user can add, edit and delete datasets, as well as manage organisation membership. <br/>
    - Editor: The user can add, edit and delete datasets, but not manage organisation membership. <br/>
    - Member: The user can view the organisation\'s private datasets, but not add new datasets or manage membership.
    <br/><br/>
    You can ignore this message if you do not wish to add the user to your organisation. <br/><br/>
    This email is the only notification you will receive from HDX regarding this user\'s request to join your
    organisation. The message has been sent to all the admins of the {org_title} organisation. <br/><br/>
    You can get in touch with the HDX team at HDX.Feedback@gmail.com if you have any questions regarding this process.
    <br/><br/>
    Best wishes, <br/>
    the HDX Team <br/>
    '''

_SUBJECT_MEMBERSHIP_APPROVED = '''Organisation membership request on HDX has been approved'''
_MESSAGE_MEMBERSHIP_APPROVED = \
'''
<br/><br/>
Your membership request to organization %(organization)s with %(role)s access has been approved.
<br/><br/>
Best wishes, <br/>
the HDX Team <br/>
'''


_SUBJECT_MEMBERSHIP_REJECTED = '''Organisation membership request on HDX has been rejected'''
_MESSAGE_MEMBERSHIP_REJECTED = \
'''
<br/><br/>
Your membership request to organization %(organization)s with %(role)s access has been rejected.
<br/><br/>
Best wishes, <br/>
the HDX Team <br/>
'''