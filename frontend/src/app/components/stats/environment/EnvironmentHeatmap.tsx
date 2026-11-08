import type { CSSProperties } from 'react';
import { ChartCard } from '../../ui/ChartCard';
import {
  ENVIRONMENT_HOURS,
  ENVIRONMENT_WEEKDAYS,
  formatCo2,
  formatOccupancy,
  heatmapColor,
  heatmapMatrix,
} from '../../../lib/environment';
import type { EnvironmentHeatmapCellDto } from '../../../types/environment';

type HeatmapMetric = 'presence' | 'co2';

interface EnvironmentHeatmapProps {
  cells: EnvironmentHeatmapCellDto[];
  metric: HeatmapMetric;
  isLoading: boolean;
  error: Error | null;
  retry: () => void;
}

function co2Color(value: number | null): string {
  if (value === null) return '#f1f5f9';
  const ratio = Math.max(0, Math.min(1, (value - 400) / 800));
  const alpha = 0.08 + ratio * 0.72;
  return `rgba(207, 108, 46, ${alpha})`;
}

function cellValue(cell: EnvironmentHeatmapCellDto | null, metric: HeatmapMetric): number | null {
  if (!cell) return null;
  return metric === 'presence' ? cell.presence_pct : cell.co2_ppm;
}

function cellLabel(value: number | null, metric: HeatmapMetric): string {
  return metric === 'presence' ? formatOccupancy(value) : formatCo2(value);
}

export function EnvironmentHeatmap({
  cells,
  metric,
  isLoading,
  error,
  retry,
}: EnvironmentHeatmapProps) {
  const matrix = heatmapMatrix(cells);
  const hasData = cells.some((cell) =>
    metric === 'presence' ? cell.presence_pct !== null : cell.co2_ppm !== null,
  );
  const title = metric === 'presence' ? 'Mapa horario de ocupación' : 'Mapa horario de CO₂';
  const subtitle =
    metric === 'presence'
      ? 'Porcentaje medio de ocupación por día de la semana y hora'
      : 'CO₂ medio por día de la semana y hora';
  const unit = metric === 'presence' ? '%' : 'ppm';

  return (
    <ChartCard
      title={title}
      subtitle={subtitle}
      unit={unit}
      isLoading={isLoading}
      error={error}
      isEmpty={!hasData}
      emptyMessage="Sin datos suficientes para construir el mapa horario."
      onRetry={retry}
      height={300}
    >
      <div className="h-full overflow-x-auto">
        <div className="min-w-[720px]">
          <div
            className="grid items-center gap-1"
            style={{ gridTemplateColumns: '44px repeat(24, minmax(0, 1fr))' }}
          >
            <span />
            {ENVIRONMENT_HOURS.map((hour) => (
              <span
                key={`hour-${hour}`}
                className="text-center text-[10px] font-semibold text-slate-500"
              >
                {hour % 3 === 0 ? hour : ''}
              </span>
            ))}
            {ENVIRONMENT_WEEKDAYS.map((weekday, weekdayIndex) => (
              <div key={weekday} className="contents">
                <span className="pr-1 text-right text-[11px] font-semibold text-slate-600">
                  {weekday}
                </span>
                {ENVIRONMENT_HOURS.map((hour) => {
                  const cell = matrix[weekdayIndex]?.[hour] ?? null;
                  const value = cellValue(cell, metric);
                  const color =
                    metric === 'presence' ? heatmapColor(value) : co2Color(value);
                  const style: CSSProperties = {
                    backgroundColor: color,
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                  };
                  return (
                    <span
                      key={`${weekday}-${hour}`}
                      title={`${weekday} ${String(hour).padStart(2, '0')}:00 · ${cellLabel(value, metric)}`}
                      aria-label={`${weekday} ${hour}:00, ${cellLabel(value, metric)}`}
                      className="block h-6 rounded-[2px]"
                      style={style}
                    />
                  );
                })}
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-end gap-2 text-[10px] text-slate-500">
            <span>Menos</span>
            <span
              className="h-2.5 w-6 rounded-[2px]"
              style={{ backgroundColor: metric === 'presence' ? 'rgba(4,151,215,0.12)' : 'rgba(207,108,46,0.12)' }}
            />
            <span
              className="h-2.5 w-6 rounded-[2px]"
              style={{ backgroundColor: metric === 'presence' ? 'rgba(4,151,215,0.45)' : 'rgba(207,108,46,0.45)' }}
            />
            <span
              className="h-2.5 w-6 rounded-[2px]"
              style={{ backgroundColor: metric === 'presence' ? 'rgba(4,151,215,0.80)' : 'rgba(207,108,46,0.80)' }}
            />
            <span>Más</span>
          </div>
        </div>
      </div>
    </ChartCard>
  );
}
