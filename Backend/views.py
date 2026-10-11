from datetime import timedelta
from functools import wraps

from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from Backend.forms import DepartmentForm, DoctorForm
from Backend.models import Deptdb, Doctordb
from Frontend.forms import BootstrapFormMixin
from Frontend.models import Appointmentdb, Blogdb, ContactMessage


def staff_required(view=None, superuser=False):
    """Allow only signed-in staff (or superusers) into the dashboard."""

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or not user.is_staff:
                messages.error(request, "Please sign in with a staff account.")
                return redirect(f"/Backend/loginpg/?next={request.path}")
            if superuser and not user.is_superuser:
                messages.error(request, "Only administrators can manage this section.")
                return redirect("indexpage")
            return func(request, *args, **kwargs)
        return wrapper

    return decorator(view) if view else decorator


def _next_or(request, default):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        return target
    return default


def _sidebar_counts():
    return {
        "pending_count": Appointmentdb.objects.filter(Status=Appointmentdb.PENDING).count(),
        "unread_count": ContactMessage.objects.filter(Read=False).count(),
        "story_count": Blogdb.objects.filter(Approved=False).count(),
    }


def _render(request, template, context=None):
    return render(request, template, {**_sidebar_counts(), **(context or {})})


# Dashboard & appointments

@staff_required
def indexpage(request):
    today = timezone.localdate()
    appointments = Appointmentdb.objects.select_related("Doctor")
    status_counts = dict(appointments.values_list("Status").annotate(n=Count("id")))
    week = [today + timedelta(days=i) for i in range(7)]
    per_day = dict(appointments.filter(Date__in=week).exclude(Status=Appointmentdb.CANCELLED)
                   .values_list("Date").annotate(n=Count("id")))
    week_load = [{"date": d, "count": per_day.get(d, 0)} for d in week]
    peak = max([d["count"] for d in week_load] + [1])
    for day in week_load:
        day["pct"] = round(day["count"] * 100 / peak)

    return _render(request, "indexpage.html", {
        "stats": {
            "today": appointments.filter(Date=today).exclude(Status=Appointmentdb.CANCELLED).count(),
            "upcoming": appointments.filter(Date__gte=today, Status__in=[Appointmentdb.PENDING,
                                                                         Appointmentdb.CONFIRMED]).count(),
            "doctors": Doctordb.objects.count(),
            "departments": Deptdb.objects.count(),
            "patients": User.objects.filter(is_staff=False).count(),
            "total": appointments.count(),
        },
        "status_counts": [(label, status_counts.get(key, 0), key) for key, label in Appointmentdb.STATUS_CHOICES],
        "week_load": week_load,
        "todays": appointments.filter(Date=today).order_by("Time")[:8],
        "recent": appointments.order_by("-Created", "-id")[:6],
    })


@staff_required
def appointments(request):
    qs = Appointmentdb.objects.select_related("Doctor").order_by("-Date", "-Time")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    when = request.GET.get("when", "")
    today = timezone.localdate()
    if query:
        qs = qs.filter(Q(Name__icontains=query) | Q(DrName__icontains=query) | Q(Phone__icontains=query)
                       | Q(Email__icontains=query) | Q(Registrations__icontains=query)
                       | Q(Department__icontains=query))
    if status:
        qs = qs.filter(Status=status)
    if when == "today":
        qs = qs.filter(Date=today)
    elif when == "upcoming":
        qs = qs.filter(Date__gte=today).order_by("Date", "Time")
    elif when == "past":
        qs = qs.filter(Date__lt=today)
    page = Paginator(qs, 15).get_page(request.GET.get("page"))
    return _render(request, "appointments.html", {
        "page": page, "query": query, "status": status, "when": when,
        "status_choices": Appointmentdb.STATUS_CHOICES,
    })


@staff_required
@require_POST
def appointment_status(request, dataid):
    appointment = get_object_or_404(Appointmentdb, id=dataid)
    status = request.POST.get("status")
    if status in dict(Appointmentdb.STATUS_CHOICES):
        appointment.Status = status
        appointment.save(update_fields=["Status"])
        messages.success(request, f"{appointment.reference} marked as {appointment.get_Status_display().lower()}.")
    return redirect(_next_or(request, "appointments"))


@staff_required(superuser=True)
@require_POST
def deleteindex(request, dataid):
    get_object_or_404(Appointmentdb, id=dataid).delete()
    messages.success(request, "Appointment deleted.")
    return redirect(_next_or(request, "appointments"))


# Departments

@staff_required(superuser=True)
def department(request):
    form = DepartmentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department added.")
        return redirect("displaydept")
    return _render(request, "department.html", {"form": form, "title": "Add department"})


deptsave = department


@staff_required
def displaydept(request):
    counts = dict(Doctordb.objects.values_list("Department").annotate(n=Count("id")))
    data = list(Deptdb.objects.all())
    for dept in data:
        dept.doctor_count = counts.get(dept.DeptName, 0)
    return _render(request, "displaydept.html", {"data": data})


@staff_required(superuser=True)
def editdept(request, dataid):
    dept = get_object_or_404(Deptdb, id=dataid)
    old_name = dept.DeptName
    form = DepartmentForm(request.POST or None, request.FILES or None, instance=dept)
    if request.method == "POST" and form.is_valid():
        dept = form.save()
        if old_name != dept.DeptName:  # doctors reference departments by name
            Doctordb.objects.filter(Department=old_name).update(Department=dept.DeptName)
        messages.success(request, "Department updated.")
        return redirect("displaydept")
    return _render(request, "department.html", {"form": form, "title": f"Edit {old_name}", "dept": dept})


updatedept = editdept


@staff_required(superuser=True)
@require_POST
def deletedept(request, dataid):
    dept = get_object_or_404(Deptdb, id=dataid)
    if Doctordb.objects.filter(Department=dept.DeptName).exists():
        messages.error(request, "Move or remove this department's doctors before deleting it.")
    else:
        dept.delete()
        messages.success(request, "Department deleted.")
    return redirect("displaydept")


# Doctors

@staff_required(superuser=True)
def doctorlist(request):
    form = DoctorForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor added.")
        return redirect("doctordisplay")
    return _render(request, "doctorlist.html", {"form": form, "title": "Add doctor"})


doctorsave = doctorlist


@staff_required
def doctordisplay(request):
    data = Doctordb.objects.annotate(
        upcoming=Count("appointments", filter=Q(appointments__Date__gte=timezone.localdate(),
                                                appointments__Status__in=[Appointmentdb.PENDING,
                                                                          Appointmentdb.CONFIRMED])))
    department = request.GET.get("department", "")
    if department:
        data = data.filter(Department=department)
    return _render(request, "doctordisplay.html", {
        "data": data, "departments": Deptdb.objects.all(), "selected_department": department})


@staff_required(superuser=True)
def doctoredit(request, dataid):
    doctor = get_object_or_404(Doctordb, id=dataid)
    form = DoctorForm(request.POST or None, request.FILES or None, instance=doctor)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Doctor updated.")
        return redirect("doctordisplay")
    return _render(request, "doctorlist.html", {"form": form, "title": f"Edit {doctor.Name}", "doctor": doctor})


doctorup = doctoredit


@staff_required(superuser=True)
@require_POST
def doctordel(request, dataid):
    get_object_or_404(Doctordb, id=dataid).delete()
    messages.success(request, "Doctor removed.")
    return redirect("doctordisplay")


# Patients, messages & stories

@staff_required(superuser=True)
def patients(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.filter(is_staff=False).order_by("-date_joined")
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query)
                             | Q(first_name__icontains=query))
    page = Paginator(users, 20).get_page(request.GET.get("page"))
    counts = dict(Appointmentdb.objects.filter(Username__in=[u.username for u in page])
                  .values_list("Username").annotate(n=Count("id")))
    for user in page:
        user.appointment_count = counts.get(user.username, 0)
    return _render(request, "patients.html", {"page": page, "query": query})


@staff_required
def inbox(request):
    page = Paginator(ContactMessage.objects.all(), 15).get_page(request.GET.get("page"))
    return _render(request, "inbox.html", {"page": page})


@staff_required
@require_POST
def message_action(request, dataid):
    msg = get_object_or_404(ContactMessage, id=dataid)
    if request.POST.get("action") == "delete":
        msg.delete()
        messages.success(request, "Message deleted.")
    else:
        msg.Read = not msg.Read
        msg.save(update_fields=["Read"])
    return redirect("inbox")


@staff_required
def stories(request):
    return _render(request, "stories.html", {"stories": Blogdb.objects.order_by("Approved", "-Created", "-id")})


@staff_required
@require_POST
def story_action(request, dataid):
    story = get_object_or_404(Blogdb, id=dataid)
    action = request.POST.get("action")
    if action == "delete":
        story.delete()
        messages.success(request, "Story deleted.")
    else:
        story.Approved = action == "approve"
        story.save(update_fields=["Approved"])
        messages.success(request, "Story published." if story.Approved else "Story hidden.")
    return redirect("stories")


# Authentication

class StaffLoginForm(BootstrapFormMixin, AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError("This account does not have staff access.", code="no_staff")


def loginpg(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("indexpage")
    form = StaffLoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = _next_or(request, "indexpage")
        return redirect(next_url if next_url == "indexpage" or next_url.startswith("/Backend/") else "indexpage")
    return render(request, "Login.html", {"form": form, "next": request.GET.get("next", "")})


loginsave = loginpg


@require_POST
def logoutpg(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("loginpg")
