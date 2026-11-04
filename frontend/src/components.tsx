import { useId, useState, type InputHTMLAttributes } from 'react';
import { Cpu, Eye, EyeOff, LockKeyhole } from 'lucide-react';

export function Brand({ compact = false }: { compact?: boolean }) {
  return <div className="brand"><span className="brand-icon"><Cpu size={23} strokeWidth={1.8} /></span>{!compact && <span>SMART CAMPUS VISION</span>}</div>;
}

export function PasswordField({ label = 'Contraseña', ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  const [visible, setVisible] = useState(false);
  const id = useId();
  return <div className="field"><label htmlFor={id}>{label}</label>
    <div className="input-icon"><LockKeyhole size={17} aria-hidden="true" />
      <input id={id} type={visible ? 'text' : 'password'} required maxLength={128} {...props} />
      <button type="button" className="reveal" aria-label={`${visible ? 'Ocultar' : 'Mostrar'} ${label.toLowerCase()}`} onClick={() => setVisible(!visible)}>
        {visible ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </div>
  </div>;
}

export function Message({ text, success = false }: { text: string; success?: boolean }) {
  if (!text) return null;
  return <div className={`message ${success ? 'success' : 'error'}`} role={success ? 'status' : 'alert'}>{text}</div>;
}
