from django.urls import path

from Frontend import views

urlpatterns = [
    path("", views.index, name="index"),
    path("aboutus/", views.aboutus, name="aboutus"),
    path("service/", views.service, name="service"),
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/<str:drname>/", views.doctors, name="doctors"),
    path("singledoctor/<int:proid>/", views.singledoctor, name="singledoctor"),
    path("singledoctor/<int:proid>/slots/", views.doctor_slots, name="doctor_slots"),
    path("appointment/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("appointment/<int:pk>/cancel/", views.appointment_cancel, name="appointment_cancel"),
    path("blog/", views.blog, name="blog"),
    path("blogsave/", views.blogsave, name="blogsave"),
    path("contact/", views.contact, name="contact"),
    path("loginfr/", views.loginfr, name="loginfr"),
    path("userlogin/", views.userlogin, name="userlogin"),
    path("registersave/", views.registersave, name="registersave"),
    path("logout/", views.logout, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profileedit/", views.profileedit, name="profileedit"),
    path("videocall/", views.videocall, name="videocall"),
]
