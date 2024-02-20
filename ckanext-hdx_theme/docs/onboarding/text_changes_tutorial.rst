ONBOARDING
===========

Changing Content from Emails or Web Pages
==========================================

Text in Emails
--------------

The email contents (the email bodies) can be found in the following folder: `Email Contents <../../../ckanext-hdx_theme/ckanext/hdx_theme/templates/email/content/onboarding>`_ .
Click on any of the HTML files from the list to see the email's text.

The subject lines are separate and can be found here, all in one file: `Email Subjects <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding/email_subjects.py>`_

Text on Web Pages
-----------------

The text on the web pages are all stored in files in the following folder: `Web Page Contents <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding>`_ .
Each file corresponds to a page from the onboarding flow (ignore the file called *__init__.py*):

*  `value_proposition.py <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding/value_proposition.py>`_ - Text from the "Value Proposition" page
*  `user_info.py <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding/user_info.py>`_ - Text from the "Personal Details" form page
*  `verify_email.py <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding/verify_email.py>`_ - Text from the "Verify Email Address" page
*  `account_validated.py <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding/account_validated.py>`_ - Text from the "Account validated" page
*  `email_subjects.py <../../../ckanext-hdx_theme/ckanext/hdx_theme/helpers/ui_constants/onboarding/email_subjects.py>`_ - This file was already mentioned above. It contains the email subjects.


Steps for Making a Change
-------------------------

#. Make sure you are logged in on Github

#. Identify the file that needs to be changed and open it on Github.

#. Click the **edit** button

   .. image:: images/edit.png

#. Make the needed changes to the file.

#. Click on the **Commit changes** button

   .. image:: images/start_commit.png

#. A popup will appear in which you should fill:

   #. Commit message - if there is a **JIRA ticket number** please start your commit message with that. Afterwards add a couple of words describing your change

   #. Use the **Create a new branch** option (there's a radio button for this) to commit your changes on a new branch and start a pull request.

   #. Give the branch a name, something like :code:`feature/HDX-9407-value-proposition-page-title`. "feature/" means it's a new feature, "bugfix/" means it's fixing an existing problem.
      So the pattern would be: :code:`CHANGE-TYPE/JIRA-TICKET-VERY-SHORT-DESCRIPTION`

   #. Click the **Propose changes** button to submit the change for review.

   .. image:: images/create_commit.png

#. Open the Pull Request. This step is less important. At this moment the changes have been saved on Github.

   #. Make sure that the "Pull Request" asks to merge the changes into the **dev** branch
   #. Click the **Create pull request** button

   .. image:: images/open_pr.png

#. Ping somebody from the dev team, to make sure they're aware of the change.  **Important step!**
