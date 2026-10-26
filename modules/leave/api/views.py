from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404

from fusion_auth.permissions import HasModuleGrant, HasPermission

from ..models import LeaveBalance, LeaveRequest
from ..serializers import LeaveBalanceSerializer, LeaveRequestSerializer


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [HasModuleGrant("leave_cell")]

    def get_permissions(self):
        perms = [HasModuleGrant("leave_cell")]
        perms.append(HasPermission("leave_cell.balances.view", "leave_cell.balances.view_all"))
        return [p() for p in perms]

    def get_queryset(self):
        principal = getattr(self.request, "principal", None)
        if principal is None or not principal.has_permission("leave_cell.balances.view_all"):
            if principal is None or not getattr(principal, "username", None):
                return LeaveBalance.objects.none()
            return LeaveBalance.objects.filter(employee_id=principal.username)
        return LeaveBalance.objects.all()


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [HasModuleGrant("leave_cell")]

    http_method_names = ["get", "post"]

    def get_permissions(self):
        perms = [HasModuleGrant("leave_cell")]
        if self.action in ["list", "retrieve"]:
            perms.append(
                HasPermission(
                    "leave_cell.requests.manage",
                    "leave_cell.requests.view_all",
                )
            )
        elif self.action == "create":
            perms.append(HasPermission("leave_cell.requests.manage"))
        elif self.action == "withdraw":
            perms.append(HasPermission("leave_cell.requests.manage"))
        return [p() for p in perms]

    def get_queryset(self):
        principal = getattr(self.request, "principal", None)
        if principal is None or not principal.has_permission("leave_cell.requests.view_all"):
            if principal is None or not getattr(principal, "username", None):
                return LeaveRequest.objects.none()
            return LeaveRequest.objects.filter(employee_id=principal.username)
        return LeaveRequest.objects.all()

    def perform_create(self, serializer):
        principal = getattr(self.request, "principal", None)
        if principal is None or not getattr(principal, "username", None):
            raise permissions.PermissionDenied("Principal username missing")
        serializer.save(employee_id=principal.username)

    @action(detail=True, methods=["post"], url_path="withdraw")
    def withdraw(self, request, pk=None):
        principal = getattr(request, "principal", None)
        if principal is None or not getattr(principal, "username", None):
            raise PermissionDenied("Principal username missing")

        try:
            with transaction.atomic():
                leave_request = LeaveRequest.objects.select_for_update().get(
                    pk=pk, employee_id=principal.username
                )
                if leave_request.status != "pending":
                    raise ValidationError("Only pending requests can be withdrawn.")
                leave_request.status = "withdrawn"
                leave_request.save(update_fields=["status", "updated_at"])
                serializer = LeaveRequestSerializer(leave_request)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except LeaveRequest.DoesNotExist:
            raise Http404
