import logging
from datetime import date as date_cls
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousFileOperation
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils._os import safe_join
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST
from django.views.static import serve

from Backend.models import Deptdb, Doctordb
from Frontend.forms import (AppointmentForm, ContactForm, LoginForm, ProfileForm, RegisterForm,
                            StoryForm)
from Frontend.models import Appointmentdb, Blogdb, Profiledb

logger = logging.getLogger(__name__)


def _approved_stories():
    return Blogdb.objects.filter(Approved=True)


def _departments_with_counts():
    counts = dict(Doctordb.objects.values_list("Department").annotate(total=Count("id")))
    departments = list(Deptdb.objects.all())
    for dept in departments:
        dept.doctor_count = counts.get(dept.DeptName, 0)
    return departments


def index(request):
    departments = _departments_with_counts()
    featured = [d for d in departments if d.doctor_count][:8] or departments[:8]
    return render(request, "index.html", {
        "departments": departments,
        "featured_departments": featured,
        "doctors": Doctordb.objects.all()[:4],
        "stories": _approved_stories()[:6],
        "doctor_total": Doctordb.objects.count(),
        "department_total": len(departments),
    })


def aboutus(request):
    return render(request, "aboutus.html", {
        "stories": _approved_stories()[:3],
        "doctor_total": Doctordb.objects.count(),
        "department_total": Deptdb.objects.count(),
    })


def service(request):
    return render(request, "service.html", {"departments": _departments_with_counts()})


def doctor_list(request):
    doctors = Doctordb.objects.all()
    query = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()
    if query:
        doctors = doctors.filter(Q(Name__icontains=query) | Q(Department__icontains=query)
                                 | Q(Language__icontains=query))
    if department:
        doctors = doctors.filter(Department=department)
    return render(request, "doctors.html", {
        "doctors": doctors,
        "departments": Deptdb.objects.all(),
        "query": query,
        "selected_department": department,
        "department_obj": Deptdb.objects.filter(DeptName=department).first() if department else None,
    })


def doctors(request, drname):
    """Legacy URL /doctors/<department>/ — kept so old links keep working."""
    return redirect(f"{reverse('doctor_list')}?department={drname}")


def singledoctor(request, proid):
    doctor = get_object_or_404(Doctordb, id=proid)
    department = Deptdb.objects.filter(DeptName=doctor.Department).first()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Please sign in to book an appointment.")
            return redirect(f"{reverse('loginfr')}?next={request.path}")
        form = AppointmentForm(request.POST, doctor=doctor)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.Doctor = doctor
            appointment.DrName = doctor.Name
            appointment.Department = doctor.Department
            appointment.Registrations = doctor.Registrations
            appointment.Username = request.user.username
            appointment.save()
            messages.success(request, "Your appointment request has been received.")
            return redirect("appointment_detail", pk=appointment.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            profile = Profiledb.objects.filter(Username=request.user.username).first()
            initial = {
                "Name": (profile and profile.Name) or request.user.get_full_name(),
                "Email": (profile and profile.Email) or request.user.email,
                "Phone": profile and profile.Phone,
            }
        form = AppointmentForm(doctor=doctor, initial=initial)

    return render(request, "singledoctor.html", {
        "single": doctor,
        "department": department,
        "form": form,
        "related": Doctordb.objects.filter(Department=doctor.Department).exclude(id=doctor.id)[:3],
    })


def doctor_slots(request, proid):
    """Booked time slots for a doctor on a given date (used to grey out the slot picker)."""
    doctor = get_object_or_404(Doctordb, id=proid)
    try:
        day = date_cls.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        return JsonResponse({"booked": []})
    booked = Appointmentdb.objects.filter(
        Doctor=doctor, Date=day, Status__in=[Appointmentdb.PENDING, Appointmentdb.CONFIRMED]
    ).values_list("Time", flat=True)
    return JsonResponse({"booked": [t.strftime("%H:%M") for t in booked if t]})


def _user_appointments(user):
    return Appointmentdb.objects.filter(Username__iexact=user.username)


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointmentdb, pk=pk)
    if not (request.user.is_staff or (appointment.Username or "").lower() == request.user.username.lower()):
        raise Http404
    return render(request, "appointment_detail.html", {"appointment": appointment})


@login_required
@require_POST
def appointment_cancel(request, pk):
    appointment = get_object_or_404(_user_appointments(request.user), pk=pk)
    if appointment.is_active:
        appointment.Status = Appointmentdb.CANCELLED
        appointment.save(update_fields=["Status"])
        messages.success(request, f"Appointment {appointment.reference} has been cancelled.")
    return redirect("profile")


def blog(request):
    form = StoryForm(initial={"Name": request.user.get_full_name() or request.user.username,
                              "Email": request.user.email} if request.user.is_authenticated else None)
    return render(request, "blog.html", {"stories": _approved_stories(), "form": form})


@require_POST
def blogsave(request):
    form = StoryForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thank you for sharing! Your story will appear once our team reviews it.")
        return redirect("blog")
    return render(request, "blog.html", {"stories": _approved_stories(), "form": form})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        if settings.CONTACT_EMAIL:
            try:
                send_mail(
                    subject=f"[Website] {msg.Subject}",
                    message=f"From: {msg.Name} <{msg.Email}> {msg.Phone}\n\n{msg.Message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    html_message=render_to_string("email_template.html", {"msg": msg}),
                )
            except Exception:
                logger.exception("Could not send contact email")
        messages.success(request, "Thanks for reaching out — our team will get back to you shortly.")
        return redirect("contact")
    return render(request, "contact.html", {"form": form})


def _safe_next(request, default="index"):
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        return target
    return reverse(default)


def loginfr(request):
    if request.user.is_authenticated:
        return redirect("profile")
    return render(request, "loginpg.html", {
        "login_form": LoginForm(request),
        "register_form": RegisterForm(),
        "next": request.GET.get("next", ""),
        "active_tab": request.GET.get("tab", "login"),
    })


@require_POST
def userlogin(request):
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
        auth_login(request, form.get_user())
        messages.success(request, f"Welcome back, {form.get_user().get_short_name() or form.get_user().username}!")
        return redirect(_safe_next(request))
    return render(request, "loginpg.html", {
        "login_form": form, "register_form": RegisterForm(),
        "next": request.POST.get("next", ""), "active_tab": "login",
    })


@require_POST
def registersave(request):
    form = RegisterForm(request.POST)
    if form.is_valid():
        user = form.save()
        Profiledb.objects.get_or_create(Username=user.username,
                                        defaults={"Name": user.first_name, "Email": user.email})
        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Your account has been created. Welcome to HolyCross!")
        return redirect(_safe_next(request))
    return render(request, "loginpg.html", {
        "login_form": LoginForm(request), "register_form": form,
        "next": request.POST.get("next", ""), "active_tab": "register",
    })


@require_POST
def logout(request):
    auth_logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("index")


@login_required
def profile(request):
    profile_obj = Profiledb.objects.filter(Username=request.user.username).first()
    appointments = _user_appointments(request.user).select_related("Doctor")
    upcoming = [a for a in appointments if a.is_active]
    past = [a for a in appointments if not a.is_active]
    return render(request, "profile.html", {
        "profile": profile_obj,
        "upcoming": sorted(upcoming, key=lambda a: (a.Date, a.Time)),
        "past": past,
    })


@login_required
def profileedit(request):
    profile_obj, _ = Profiledb.objects.get_or_create(
        Username=request.user.username,
        defaults={"Name": request.user.get_full_name(), "Email": request.user.email})
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "profileedit.html", {"form": form, "profile": profile_obj})


@login_required
def videocall(request):
    return render(request, "videocall.html", {
        "zego_app_id": settings.ZEGO_APP_ID if settings.ZEGO_APP_ID.isdigit() else "",
        "zego_server_secret": settings.ZEGO_SERVER_SECRET,
    })


@cache_control(public=True, max_age=60 * 60 * 24 * 7)
def media(request, path):
    """Serve uploaded files from the upload root first, then the bundled media folder."""
    for root in dict.fromkeys([Path(settings.UPLOAD_ROOT), Path(settings.MEDIA_ROOT)]):
        try:
            full_path = Path(safe_join(root, path))
        except SuspiciousFileOperation:
            raise Http404
        if full_path.is_file():
            return serve(request, path, document_root=root)
    raise Http404


def page_not_found(request, exception):
    return render(request, "404.html", status=404)
