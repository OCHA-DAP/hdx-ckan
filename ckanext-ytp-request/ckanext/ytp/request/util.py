import logging

log = logging.getLogger(__name__)

_SUBJECT_MEMBERSHIP_REQUEST = u'''{user_fullname} sent a request to join your organisation on HDX'''
_MESSAGE_MEMBERSHIP_REQUEST = \
    u'''
    <br/>
    Dear Admin of {org_title} organisation,
    
    <br/><br/>{user_fullname} ( {user_email} ) has requested to join your organisation on HDX, along with the following 
    message: 
    <br/><span style="margin-left:2em"><i>{user_message}</i></span>
    <br/><br/>Please be aware that anyone added to your organisation on HDX <b>can view the organisation's private 
    datasets</b>. 
    
    <br/><br/>If you can confirm that this user works for your organisation or is in your trusted network, then you may 
    approve the request. If you cannot verify who the user is, you should decline the request. Please do not approve 
    membership requests for people outside your trusted network. 
        
    <br/><br/><a href="{org_add_member_url}">Click here to approve or decline the membership</a> request, listed under 
    "Pending approval".
    
    <br/><br/>If approved, you can assign the user one of the following roles:
    <ul>
    <li>Admin: The user can add, edit and delete datasets, and manage organisation membership. </li>
    <li>Editor: The user can add, edit and delete datasets. They cannot manage organisation membership. </li>
    <li>Member: The user can view the organisation's private datasets. They cannot add new datasets or manage 
    membership.</li>
    </ul>
    
    For more details on how to manage organisational members, 
    <a href="https://gdoc.pub/doc/e/2PACX-1vRh4Dr3zIQrKQt__HPs_kwC_9qyIr25naivppxFP16JSA0HbT-SRWcMKhsMA91SnY589q7BZgNf86q2">
    please refer to this document</a>. Feel free to contact the HDX team at <a href="mailto:hdx@un.org">hdx@un.org</a> 
    if you have any questions regarding this process.
    
    <br/><br/>This message has been sent to all the admins of your organisation on HDX.
    
    <br/><br/>
    Best wishes, <br/>
    the HDX Team <br/> 
    '''

_SUBJECT_MEMBERSHIP_APPROVED = u'''Organisation membership request on HDX has been approved'''
_MESSAGE_MEMBERSHIP_APPROVED = \
    u'''
    <br/><br/>
    Your membership request to organisation {organization} with {role} access has been approved.
    <br/><br/>
    Best wishes, <br/>
    the HDX Team <br/>
    '''

_SUBJECT_MEMBERSHIP_REJECTED = u'''Organisation membership request on HDX has been rejected'''
_MESSAGE_MEMBERSHIP_REJECTED = \
    u'''
    <br/><br/>
    Your membership request to organisation {organization} with {role} access has been rejected.
    <br/><br/>
    Best wishes, <br/>
    the HDX Team <br/>
    '''
