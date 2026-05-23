# The Avature SaaS Platform

This document is intended to onboard developers and code-assisting agents about the Avature SaaS platform, in order to
give context about how users will interact with the Copilot for creating portals (a.k.a. Portals Agent).

## About Avature
Avature is a highly configurable enterprise SaaS platform designed for organizations to streamline and maximize their talent acquisition and talent management processes. The platform supports a wide range of recruiting and HR operations—from sourcing and screening to onboarding, engagement, internal mobility, and analytics—implemented through different solutions, including Candidate Relationship Management (CRM), Applicant Tracking System (ATS), video interviewing, events management, onboarding, and performance management. Solutions can be implemented within Avature's core application or in external portal applications.

## Records
At the core of Avature's system is a flexible data model based on records. Avature records  are divided into record types that represent real-world concepts. Each individual record is an entity in the system that stores structured and unstructured data about a single thing that falls under the category of a record type. Organizations can configure the layout of each record type to capture information in a way that is specific to their purpose.
Avature offers the following record types:
Person records represent people related to the organization, such as candidates, employees, or users. These records store personal and work data about a person, such as contact information, employment history, qualifications, interview notes, performance evaluations, and other relevant data.
Company records represent entire organizations, such as partner companies, agencies, consulting firms, vendors, and competitors. These records can include lists of current employees made up of person records and lists of open jobs made up of object records.
Object records represent the different business activities that an organization manages. Organizations can implement one or multiple object record types and customize their name and the information they store. Some of the most common use cases of object records include jobs, pipelines, events, and projects.
### Linking Records
Person records can be linked to object records to represent a relationship between the two. For example, when a candidate applies to a job, the person record representing the candidate is linked to the object record representing the job.
When a person and an object record are linked, the system creates a relationship between them that allows users to manage the person-object workflow that guides the person record through a given process. These relationships are visible from the person record, and they can store forms that are attached through the workflow.
Optionally, organizations can choose to implement one or more compound record types to materialize the relationship between person records and one type of object records in a new, individual record. The type of information stored in compound records can be customized depending on the process they represent and the organization's needs, allowing users to capture more detailed information about the relationship than using a person-object relationship. A common example of a compound record is an application record that represents a relationship between a candidate and a job.

##Lists
Users can create lists to gather records of a specific type that meet certain criteria set up through filters—for example, a list of candidates in the "Interview" step for a job. Any data stored in a record type can be used as a column in a list of records of that type, and you can customize how the information is displayed. Lists can also be used to perform mass actions on multiple records at the same time (e.g., send emails, export data, update steps). Users can share lists with other users through the platform or export them.

##Views
Record views are snapshots of record information that capture a record's data at a certain point in time. Users create views using fields from a record type, and when that view is related to a specific record, the system completes the view with the values stored in the record's fields. Views can be styled with special formatting or branding, and the fields can be filled out using predefined text, allowing organizations to use views to create customized offer letters or legal documents. To export views, users can download or email them as static PDF or HTML files.

## Fields, Forms, and Notes
There are additional methods of collecting and organizing data in records:
### Forms:
Users can create forms with custom fields that collect data about people, business activities, or organizations, and then add them to the corresponding record. Forms can be attached to a record manually from a record or as a mass action, either from a list or from the result of an advanced search. Additionally, organizations can configure import services in Avature and use them to complete forms as a mass action. Users can use workflow actions that add the form automatically to records. Optionally, they can configure conditional step updates to trigger actions based on the content of the form.
Depending on the attachment process, forms can appear in the record's Forms panel or in the person-object relationship that is created when two records are linked.
Forms can be completed either by the user who attached the form or by other stakeholders, who are notified through a form completion request.

### Files:
Users can attach files to records to add supporting documentation, such as a resume or a cover letter. The name and content of the files attached to records can be searched using advanced search.
Users can attach files manually from records or set a workflow action that attaches a record view as a file to a record. Additionally, files are attached automatically when Avature imports information from third-party systems to a record, when a person record is created from a portal, or when person records are created based on a file from the core application, WebSources, the Avature Import Extension, or the Avature Dropbox.
Organizations can configure multiple file types in Avature to categorize the files attached to records. When there are multiple files of the same type, users can mark one as preferred.
To export these files, users can download them or send them as attachments in an email.

### Notes:
Users can add notes to include comments or additional information in a record that doesn't belong in the record's fields or in a form. These notes can include mentions to other users, allowing users to use notes as messages to other users about that specific record.
Notes can be added manually from a record or as a mass action from a list or the result of an advanced search.
Organizations can configure multiple note types in Avature to categorize notes according to their purpose.

## Search Capabilities
Avature offers powerful search tools to find and segment records:

### Advanced Search
Advanced search allows users to build complex search strings using field conditions, workflow status, tags, and other metadata. Using advanced search, users can find records in Avature or items in records, such as files, notes, or the value in a record field.
Advanced search supports Boolean searches—a keyword-based search language often used in sourcing that allows users to join search terms and build complex and specific searches. Users can write queries in advanced search using Boolean logic (e.g., `("java developer" OR "software engineer") AND (Germany OR "remote work") AND NOT intern`).
Advanced search also supports semantic suggestions—keywords that the system proposes as synonyms or alternatives based on an ontology of position titles and skills, as well as a computer model of the relations between them. Semantic suggestions are available in English, German, French, Spanish, Italian, Dutch, Japanese, Chinese, and Portuguese.

### Quick Search
Quick Search is a tool to perform short, keyword-based searches to quickly find records and Avature resources (like libraries and settings pages) from the top bar.

### WebSources
WebSources is a sourcing tool that runs simultaneous searches across internal databases (existing person records in Avature) and external databases (such as paid job boards, free websites, and ATSs) to find candidates that match the criteria you specify. Users can save WebSources searches to re-run them later with the same or similar criteria, or they can configure Avature to run the search automatically on a schedule.

## Workflows and Automation
Workflows are a series of steps that a person or an object record goes through as part of your organization's work processes. Different workflow types represent different work processes:
Object workflows represent the cycle of a business activity. There is one type of object workflow for each object record type in Avature.
Person-object workflows represent the different steps that people go through after being linked to a business activity.
Person workflows represent processes that person records go through that are independent from business activities (for example, opt-in or opt-out processes).
To reflect how a process is progressing, a record's step can be updated either manually from a record or automatically when the record meets certain conditions. Additionally, a step can have a precondition that the record must meet to be moved to it—for example, a form must be completed, or a field must have a specific value.
Organizations can configure actions in workflow steps to automate and optimize work processes. Workflows can trigger and perform the actions automatically, or the action can remain in the corresponding workflow panel of each record for the user to complete it manually. Actions can have conditions configured that work as prerequisites for the action: if the record doesn't meet the condition, the action won't be triggered.

## Portals
Organizations can request that Avature configure highly customizable portals so that people can manage information in Avature without accessing the platform. The three types of portals available are sign-up pages, record update portals, and portal applications. Alternatively, organizations can choose to implement the portal apps builder so that users can create portals themselves.
Non-Avature users can access the portals through a link or an invitation, or they can access with their own credentials as portal users.

### Sign-up Pages
Sign-up pages are one-page portals that core application users can create and customize themselves. They are designed for people to add their personal information to Avature. For example, they can sign up for an organization's talent community, an event, or a job opportunity.

### Record Update Portals
Record update portals are one-page portals that users can create and customize themselves. They are designed for people to update their personal information in Avature. For example, people in a talent community can update their information, or organizations can request additional information about candidates who applied to a job.

### Portal Applications
Organizations can implement complex custom portals to gather and manage people's information and to display information from records created in the core application. These portal applications can include multiple pages and integrate multiple functionalities, as well as include custom layouts and branding. Common types of portal applications include hiring manager sites, career sites, referrals portals, time slot portals, live video portals, and recorded video portals.

## Communication & Engagement

Avature facilitates communications with different stakeholders, such as candidates, prospects, clients, employees, or coworkers. These communications can then be tracked from the sender and recipient's person records, as the actions are logged in each record journal and the messages appear in the Messages panel.
Users can choose between multiple communication methods:
Emails: Emails can be standardized using templates with variants that adapt to the recipient. Users can also configure multiple email addresses in a single account to choose between them in different situations.
SMS: Organizations can choose to set up an SMS service with a third-party vendor. SMS can also be standardized using templates with variants that adapt to the recipient.
WhatsApp messages and WeChat messages: Organizations can integrate Avature with either of these platforms to send messages from Avature through the apps. These communications must use pre-approved message templates.
All these communication methods can be triggered either manually, from a record or as a mass action using lists or advanced search, or automatically, using a workflow step action. Additionally, organizations can set automatic email campaigns using scheduled actions.
Avature also offers other communication options that send specific information:
Portal access requests: SMS or emails sent to invite people to access a portal, for example, to update their contact information.
Form completion requests: Messages asking someone to complete a form that captures additional information about a record. Once completed, the form is attached to the corresponding record.
Events: After creating an event using the Avature calendar, users can send invitations to the people they want to attend.
Avature video: Avature video interviews allow users to connect with people through recorded and live video meetings. After creating one of these meetings using the Avature calendar, users can send invitations to the guests either manually or via email or SMS.
Social media: Organizations can integrate Avature with professional and social media platforms like Facebook, LinkedIn, and X. From Avature, users can post jobs on these platforms to reach out to potential candidates.
Additionally, users can use the Avature Dropbox to save the conversations that happen outside Avature in a specific person or company record in the system. By sending an email to a special address, users can create and update records in Avature.

## Additional Solutions

### Avature DNA
Avature DNA is Avature's professional social platform meant for employees to engage with each other and create an internal corporate online community. This external platform allows departments to forge connections and colleagues to discover each other, fostering internal communication across the organization. Avature DNA can also support recruitment processes by automatically announcing promotions, new hires, and internal mobility changes.

### Avature Learning
Avature Learning is a solution designed for organizations to share instructional material with their employees, helping streamline the learning experiences required for onboarding and internal mobility processes. It is an external platform built within DNA where HR employees can assign learning units for employees to develop a specific area of knowledge. The learning units created can be curated and promoted to users based on system-generated feedback, AI-driven algorithms, and HR strategy.

### Avature Calendar
Avature Calendar is Avature's in-house calendar application designed for users to manage their schedules and tasks using one of the following types of calendar items:
Tasks that you can assign to yourself or to another user.
Events that you can invite people to attend at a certain time and location.
Time slots that you can publish in portals for people to self-schedule their attendance at events.
Event groups, which are a series of events created together because they share related records and guests. (For example, a series of interviews for a candidate.)
Scheduling polls, where participants provide their availability, and either a user or the system automatically schedules an event using the first slot available for all participants.
Calendar items can be assigned to users and related to records they reference. Events and scheduling polls can also have guests, who receive notifications and reminders for the event. Calendar items can also be shared with other users, who can subscribe to calendars created by others.
Avature Calendar can be integrated with external calendars such as Google Calendar and Microsoft 365 to combine availability information.

### Avature Video
Avature offers two solutions to support video interviews: Avature Live Video and Avature Recorded Video.
Avature Live Video allows Avature users to invite people to a video meeting through events or time slots created in the Avature calendar. Participants receive a URL to the live video portal where they can access the meeting room, and assignees can monitor who enters the meeting room. Avature provides its native, built-in video tool, but organizations can integrate with either Microsoft Teams or Zoom. Using Avature's built-in video conferencing tool, assignees can also take notes in a form, record the video meeting, or access other relevant information while the video meeting is underway.
Avature Recorded Video allows users to design interactive interviews for candidates to access through a recorded video portal. This portal can store recorded video for both interviewers and candidates and allow candidates to record their answers to be saved in the core application. This solution uses Avature's built-in video tool and is not available to integrate with external video providers.

## Reporting and Analytics

### Reports
Avature's reporting capabilities allow organizations to thoroughly track different metrics that can help measure progress and performance and identify areas for improvement. Avature reports, common to all organizations and designed to report on core Avature functionality, display metrics about an organization's data graphically in bar charts, line charts, tables and more. They can be used to report on a wide range of information, from the number of open jobs to the sources of candidates in your system.
In addition to existing reports, Avature offers custom reports: reports built by Avature for your organization or built by users with access to the custom report builder. Custom reports can pull data from different sources, use complex filters, and perform operations on the data to get a specific slice of information. How the information is presented in custom reports can also be customized to include one or multiple views inserted in a specific layout.

### Dashboards
Dashboards are information management tools that help organize data and other Avature features for easy access. They contain multiple individual dashlets for lists, reports, or indicators that can display up-to-date performance statistics, charts, and more.
There are different types of dashboards: standard dashboards, accessible from the main menu, record dashboards, configured in a record's Dashboard panel, and home dashboards, designed to be used as Avature's home page.
The information captured in each dashboard depends on their purpose.

## Permissions and Roles

Avature features are governed by role-based access control. This means that organizations can grant different permissions to the roles that are assigned to users. These permissions determine the level of access a user has to the system, which helps ensure compliance and security.
