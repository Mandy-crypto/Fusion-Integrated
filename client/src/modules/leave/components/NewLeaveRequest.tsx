import { useState } from "react";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { useAuth } from "../../../auth/AuthProvider";
import { http, errorMessage } from "../../../lib/http";
import { notifications } from "@mantine/notifications";
import { Button, Modal, TextInput, Select, Textarea } from "@mantine/core";

export function NewLeaveRequest() {
  const { can } = useAuth();
  const queryClient = useQueryClient();
  const [opened, setOpened] = useState(false);
  const [type, setType] = useState<string | null>("CL");
  const [startDate, setStartDate] = useState<string | null>(null);
  const [endDate, setEndDate] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [dayPeriod, setDayPeriod] = useState<"full_day" | "first_half" | "second_half">("full_day");

  const mutation = useMutation({
    mutationFn: async () => {
      if (!type || !startDate || !endDate) throw new Error("Missing required fields");
      await http.post("/leave/requests/", {
        leave_type: type,
        start_date: startDate,
        end_date: endDate,
        reason,
        day_period: dayPeriod,
      });
    },
    onSuccess: () => {
      notifications.show({ title: "Success", message: "Leave request submitted" });
      setOpened(false);
      setType("CL");
      setStartDate(null);
      setEndDate(null);
      setReason("");
      setDayPeriod("full_day");
      queryClient.invalidateQueries({ queryKey: ["leave-requests"] });
    },
    onError: (e) => {
      notifications.show({ title: "Error", message: errorMessage(e), color: "red" });
    },
  });

  if (!can("leave_cell.requests.manage")) return null;

  const handleSubmit = () => {
    mutation.mutate();
  };

  const isSubmitDisabled = !type || !startDate || !endDate || (endDate && startDate && endDate < startDate) || mutation.isPending;

  const handleTypeChange = (value: string | null) => {
    setType(value);
    if (value !== "CL") {
      setDayPeriod("full_day");
    }
  };

  const handleDayPeriodChange = (value: string | null) => {
    if (value === null) {
      setDayPeriod("full_day");
    } else {
      // Type assertion is safe because the Select options only provide valid values
      setDayPeriod(value as "full_day" | "first_half" | "second_half");
    }
  };

  return (
    <>
      <Button onClick={() => setOpened(true)}>New Leave Request</Button>
      <Modal opened={opened} onClose={() => setOpened(false)} title="New Leave Request">
        <Select
          label="Type"
          data={[
            { value: "CL", label: "CL" },
            { value: "RH", label: "RH" },
            { value: "SCL", label: "SCL" },
            { value: "EL", label: "EL" },
            { value: "COL", label: "COL" },
            { value: "VL", label: "VL" },
          ]}
          value={type}
          onChange={handleTypeChange}
          required
        />
        {type === "CL" && (
          <Select
            label="Day Period"
            data={[
              { value: "full_day", label: "Full Day" },
              { value: "first_half", label: "First Half" },
              { value: "second_half", label: "Second Half" },
            ]}
            value={dayPeriod}
            onChange={handleDayPeriodChange}
            required
            mt="sm"
          />
        )}
        <TextInput
          label="Start Date"
          type="date"
          value={startDate ?? ""}
          onChange={(e) => setStartDate(e.currentTarget.value)}
          required
          mt="sm"
        />
        <TextInput
          label="End Date"
          type="date"
          value={endDate ?? ""}
          onChange={(e) => setEndDate(e.currentTarget.value)}
          required
          mt="sm"
        />
        <Textarea
          label="Reason"
          value={reason}
          onChange={(e) => setReason(e.currentTarget.value)}
          mt="sm"
        />
        <Button onClick={handleSubmit} fullWidth mt="md" disabled={isSubmitDisabled} loading={mutation.isPending}>
          Submit
        </Button>
      </Modal>
    </>
  );
}
