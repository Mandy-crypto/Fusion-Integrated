from rest_framework import serializers
from .models import LeaveRequest, LeaveBalance, LeaveType, LeaveDayPeriod
from .domain.overlap import requests_overlap

class LeaveBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveBalance
        fields = ['employee_id', 'leave_type', 'balance', 'last_updated']
        read_only_fields = fields

class LeaveRequestSerializer(serializers.ModelSerializer):
    day_period = serializers.ChoiceField(
        choices=LeaveDayPeriod.choices,
        default=LeaveDayPeriod.FULL_DAY,
        required=False,
    )

    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee_id', 'leave_type', 'start_date', 'end_date', 'reason', 'status', 'created_at', 'updated_at', 'day_period']
        read_only_fields = ['id', 'employee_id', 'status', 'created_at', 'updated_at']

    def validate(self, attrs):
        # Ensure dates are present
        start_date = attrs.get('start_date') or getattr(self.instance, 'start_date', None)
        end_date = attrs.get('end_date') or getattr(self.instance, 'end_date', None)
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError('End date must be after start date.')

        # Validate day_period rules
        period = attrs.get('day_period', LeaveDayPeriod.FULL_DAY)
        leave_type = attrs.get('leave_type') or getattr(self.instance, 'leave_type', None)
        if period in {LeaveDayPeriod.FIRST_HALF, LeaveDayPeriod.SECOND_HALF}:
            if leave_type != LeaveType.CL:
                raise serializers.ValidationError('Half-day periods are only allowed for CL.')
            if start_date != end_date:
                raise serializers.ValidationError('Half-day periods are only allowed for single-day requests.')
        else:
            # For non-CL, enforce full_day
            if leave_type and leave_type != LeaveType.CL:
                if period != LeaveDayPeriod.FULL_DAY:
                    raise serializers.ValidationError('Non-CL requests must use full_day period.')
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'principal'):
            raise serializers.ValidationError('Missing principal information.')
        employee_id = getattr(request.principal, 'username', None)
        if not employee_id:
            raise serializers.ValidationError('Principal username is required.')

        # Override employee_id to ensure safety
        validated_data['employee_id'] = employee_id

        # Check for overlapping pending/approved requests
        new_start = validated_data['start_date']
        new_end = validated_data['end_date']
        new_type = validated_data['leave_type']
        new_period = validated_data.get('day_period', LeaveDayPeriod.FULL_DAY)

        overlapping_qs = LeaveRequest.objects.filter(
            employee_id=employee_id,
            status__in=['pending', 'approved'],
        )
        for existing in overlapping_qs:
            if requests_overlap(
                new_start,
                new_end,
                existing.start_date,
                existing.end_date,
                new_type,
                existing.leave_type,
                new_period,
                existing.day_period,
            ):
                raise serializers.ValidationError('Leave request overlaps with an existing pending or approved request.')

        return super().create(validated_data)
