"use client";

import { FormEvent, useEffect, useState } from "react";

import { doctorApi, patientApi, vitalsApi } from "@/lib/api";
import { ApiError } from "@/lib/api-client";
import { DoctorProfileRead, PatientProfileRead, VitalSignsCreate } from "@/types";
import { VitalsLine } from "@/components/ui/VitalsLine";

export default function NurseDashboardPage() {
  const [patients, setPatients] = useState<PatientProfileRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFormPatientId, setActiveFormPatientId] = useState<string | null>(null);
  const [activeFormMode, setActiveFormMode] = useState<"vitals" | "assign" | null>(null);

  const load = () => {
    setIsLoading(true);
    patientApi
      .listForNurse()
      .then(setPatients)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load your patients."))
      .finally(() => setIsLoading(false));
  };

  useEffect(load, []);

  function openForm(patientId: string, mode: "vitals" | "assign") {
    setActiveFormPatientId((prev) => (prev === patientId && activeFormMode === mode ? null : patientId));
    setActiveFormMode((prev) => (activeFormPatientId === patientId && prev === mode ? null : mode));
  }

  if (isLoading) return <VitalsLine animated />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-medium">Assigned patients</h1>
        <p className="text-sm text-muted mt-1">Record vitals and route patients to a doctor.</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="card divide-y divide-hairline">
        {patients.length === 0 ? (
          <p className="text-sm text-muted p-6">No patients assigned to you right now.</p>
        ) : (
          patients.map((patient) => (
            <div key={patient.patientId} className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">
                    {patient.firstName} {patient.lastName}
                  </p>
                  <p className="text-sm text-muted mt-0.5">
                    {patient.assignedDoctorId ? "Assigned to a doctor" : "Not yet assigned to a doctor"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => openForm(patient.patientId, "vitals")}
                    className="rounded border border-hairline px-3 py-1.5 text-sm hover:bg-vellum-100"
                  >
                    Record vitals
                  </button>
                  <button
                    onClick={() => openForm(patient.patientId, "assign")}
                    className="rounded bg-clinical-700 text-vellum px-3 py-1.5 text-sm"
                  >
                    Assign doctor
                  </button>
                </div>
              </div>

              {activeFormPatientId === patient.patientId && activeFormMode === "vitals" && (
                <RecordVitalsForm
                  patientId={patient.patientId}
                  onDone={() => {
                    setActiveFormPatientId(null);
                    setActiveFormMode(null);
                  }}
                />
              )}

              {activeFormPatientId === patient.patientId && activeFormMode === "assign" && (
                <AssignDoctorForm
                  patientId={patient.patientId}
                  onDone={() => {
                    setActiveFormPatientId(null);
                    setActiveFormMode(null);
                    load();
                  }}
                />
              )}
            </div>
          ))
        )}
      </section>
    </div>
  );
}

function RecordVitalsForm({ patientId, onDone }: { patientId: string; onDone: () => void }) {
  const [form, setForm] = useState<Omit<VitalSignsCreate, "patientId">>({
    bloodPressureSystolic: 120,
    bloodPressureDiastolic: 80,
    heartRate: 70,
    temperatureCelsius: 37.0,
    respiratoryRate: 16,
    oxygenSaturation: 98,
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await vitalsApi.record({ patientId, ...form });
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't record vitals.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 pt-4 border-t border-hairline space-y-4">
      {error && (
        <p className="text-sm text-danger bg-red-50 border border-danger/20 rounded px-3 py-2" role="alert">
          {error}
        </p>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="field-label">BP systolic</label>
          <input
            type="number"
            required
            className="field-input"
            value={form.bloodPressureSystolic}
            onChange={(e) => update("bloodPressureSystolic", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="field-label">BP diastolic</label>
          <input
            type="number"
            required
            className="field-input"
            value={form.bloodPressureDiastolic}
            onChange={(e) => update("bloodPressureDiastolic", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="field-label">Heart rate</label>
          <input
            type="number"
            required
            className="field-input"
            value={form.heartRate}
            onChange={(e) => update("heartRate", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="field-label">Temp (°C)</label>
          <input
            type="number"
            step="0.1"
            required
            className="field-input"
            value={form.temperatureCelsius}
            onChange={(e) => update("temperatureCelsius", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="field-label">Respiratory rate</label>
          <input
            type="number"
            required
            className="field-input"
            value={form.respiratoryRate}
            onChange={(e) => update("respiratoryRate", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="field-label">O2 saturation (%)</label>
          <input
            type="number"
            required
            className="field-input"
            value={form.oxygenSaturation}
            onChange={(e) => update("oxygenSaturation", Number(e.target.value))}
          />
        </div>
      </div>

      <div>
        <label className="field-label">Notes</label>
        <textarea
          className="field-input"
          rows={2}
          value={form.notes ?? ""}
          onChange={(e) => update("notes", e.target.value)}
        />
      </div>

      <button type="submit" className="btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Save vitals"}
      </button>
    </form>
  );
}

function AssignDoctorForm({ patientId, onDone }: { patientId: string; onDone: () => void }) {
  const [doctors, setDoctors] = useState<DoctorProfileRead[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    doctorApi
      .search({ availableOnly: true })
      .then(setDoctors)
      .catch(() => setError("Couldn't load available doctors."))
      .finally(() => setIsLoading(false));
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedDoctorId) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await patientApi.assignDoctor(patientId, selectedDoctorId);
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't assign this doctor.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 pt-4 border-t border-hairline space-y-4">
      {error && <p className="text-sm text-danger">{error}</p>}

      {isLoading ? (
        <VitalsLine animated />
      ) : (
        <div>
          <label className="field-label">Doctor</label>
          <select
            required
            className="field-input"
            value={selectedDoctorId}
            onChange={(e) => setSelectedDoctorId(e.target.value)}
          >
            <option value="" disabled>
              Select a doctor
            </option>
            {doctors.map((doctor) => (
              <option key={doctor.doctorId} value={doctor.userId}>
                {doctor.specialty} — {doctor.licenseNumber}
              </option>
            ))}
          </select>
        </div>
      )}

      <button type="submit" className="btn-primary" disabled={isSubmitting || !selectedDoctorId}>
        {isSubmitting ? "Assigning…" : "Assign doctor"}
      </button>
    </form>
  );
}