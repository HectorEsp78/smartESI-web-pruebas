import { aemetNotice } from '../../../lib/weather';
import type { AemetAvailabilityDto, AemetLatestDto } from '../../../types/weather';

interface WeatherAemetNoticeProps {
  availability: AemetAvailabilityDto;
  latest: AemetLatestDto;
}

const TONE_CLASS = {
  info: 'border-slate-200 bg-slate-50 text-slate-700',
  warning: 'border-amber-200 bg-amber-50 text-amber-900',
};

export function WeatherAemetNotice({ availability, latest }: WeatherAemetNoticeProps) {
  const notice = aemetNotice(availability, latest);
  if (!notice) return null;

  return (
    <div role="status" className={`rounded-md border px-4 py-3 text-sm ${TONE_CLASS[notice.tone]}`}>
      <p className="font-semibold">{notice.title}</p>
      <p className="mt-0.5 text-xs">{notice.detail}</p>
    </div>
  );
}
