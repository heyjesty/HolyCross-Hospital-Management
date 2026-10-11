from django.urls import path

from Backend import views

urlpatterns = [
    # Dashboard & appointments
    path("indexpage/", views.indexpage, name="indexpage"),
    path("appointments/", views.appointments, name="appointments"),
    path("appointments/<int:dataid>/status/", views.appointment_status, name="appointment_status"),
    path("deleteindex/<int:dataid>/", views.deleteindex, name="deleteindex"),

    # Departments
    path("department/", views.department, name="department"),
    path("deptsave/", views.deptsave, name="deptsave"),
    path("displaydept/", views.displaydept, name="displaydept"),
    path("editdept/<int:dataid>/", views.editdept, name="editdept"),
    path("updatedept/<int:dataid>/", views.updatedept, name="updatedept"),
    path("deletedept/<int:dataid>/", views.deletedept, name="deletedept"),

    # Doctors
    path("doctorlist/", views.doctorlist, name="doctorlist"),
    path("doctorsave/", views.doctorsave, name="doctorsave"),
    path("doctordisplay/", views.doctordisplay, name="doctordisplay"),
    path("doctoredit/<int:dataid>/", views.doctoredit, name="doctoredit"),
    path("doctorup/<int:dataid>/", views.doctorup, name="doctorup"),
    path("doctordel/<int:dataid>/", views.doctordel, name="doctordel"),

    # Patients, messages & stories
    path("patients/", views.patients, name="patients"),
    path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:dataid>/", views.message_action, name="message_action"),
    path("stories/", views.stories, name="stories"),
    path("stories/<int:dataid>/", views.story_action, name="story_action"),

    # Authentication
    path("", views.loginpg),
    path("loginpg/", views.loginpg, name="loginpg"),
    path("loginsave/", views.loginsave, name="loginsave"),
    path("logoutpg/", views.logoutpg, name="logoutpg"),
]
