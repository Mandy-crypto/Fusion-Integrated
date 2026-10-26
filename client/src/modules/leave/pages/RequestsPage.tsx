import type { Column } from "../../../ui/components/DataTable";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { http, errorMessage } from "../../../lib/http";
import { PageHeader } from "../../../ui/components/PageHeader";
import { DataTable } from "../../../ui/components/DataTable";
import { ErrorState } from "../../../ui/components/ErrorState";
import { NewLeaveRequest } from "../components/NewLeaveRequest";
import { useAuth } from "../../../auth/AuthProvider";
import { notifications } from "@mantine/notifications";
import { Button } from "@mantine/core";

interface LeaveRequest {
  id: number;
  employee_id: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface CursorPage {
  results: LeaveRequest[];
  next: string | null;
  previous: string | null;
}

export default function RequestsPage() {
  const { data, error, isLoading } = useQuery<CursorPage>({
    queryKey: ["leave-requests"],
    queryFn: async () => {
      const res = await http.get("/leave/requests/");
      return res.data;
    },
  });

  const queryClient = useQueryClient();
  const auth = useAuth();

  const withdrawMutation = useMutation({
    mutationFn: async (id: number) => {
      return await http.post(`/leave/requests/${id}/withdraw/`);
    },
    onSuccess: () => {
      notifications.show({
        title: "Success",
        message: "Leave request withdrawn.",
        color: "green",
      });
      queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
    },
    onError: (e: any) => {
      notifications.show({
        title: "Error",
        message: errorMessage(e),
        color: "red",
      });
    },
  });

  const columns: Column<LeaveRequest>[] = [
    { key: "id", header: "ID" },
    { key: "employee_id", header: "Employee ID" },
    { key: "leave_type", header: "Leave Type" },
    { key: "start_date", header: "Start Date" },
    { key: "end_date", header: "End Date" },
    { key: "reason", header: "Reason" },
    { key: "status", header: "Status" },
    { key: "created_at", header: "Created At" },
    { key: "updated_at", header: "Updated At" },
    {
      key: "actions",
      header: "Actions",
      render: (row) => {
        if (
          row.status !== "pending" ||
          !auth.can("leave_cell.requests.manage") ||
          auth.session?.user.username !== row.employee_id
        ) {
          return null;
        }
        return (
          <Button
            size="xs"
            color="red"
            variant="light"
            onClick={() => withdrawMutation.mutate(row.id)}
            disabled={withdrawMutation.isPending}
          >
            Withdraw
          </Button>
        );
      },
    },
  ];

  const rows = data?.results ?? [];

  return (
    <>
      <PageHeader
        title="Leave Requests"
        subtitle="Full leave-policy validation and approvals are not implemented."
        action={<NewLeaveRequest />}
      />
      {error && <ErrorState error={error} />}
      <DataTable
        rows={rows}
        columns={columns}
        loading={isLoading}
        rowKey={(r) => r.id}
        empty={{
          title: "No requests found",
          description: "You have not submitted any leave requests.",
        }}
      />
    </>
  );
}
