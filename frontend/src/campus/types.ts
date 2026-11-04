export type Interval = { weekday: number; start: string; end: string };
export type Classroom = {
  id: number; name: string; kind: 'classroom' | 'lab'; kind_label: string; location: string;
  capacity: number | null; active: boolean; equipment: string[]; availability: Interval[];
  camera: string; camera_label: string; camera_display: string;
  validated_capacity: number | null; validated_by_name: string | null; capacity_validated_at: string | null;
};
export type Teacher = { id: number; name: string; email: string; active: boolean };
export type Subject = { id: number; code: string; name: string; active: boolean };
export type Course = {
  id: number; code: string; name: string; subject: number; teacher: number; teacher_name: string;
  subject_name: string; enrollment: number; active: boolean; required_equipment: string[]; meetings: Interval[];
};
export type Validation = { id: number; value: number; note: string; actor_name: string; created_at: string };
export type Activity = { id: number; created_at: string; people: number; capacity: number | null; occupancy: number | null };
