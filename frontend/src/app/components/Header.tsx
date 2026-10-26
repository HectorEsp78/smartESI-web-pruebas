import { motion } from 'motion/react';
import { Link } from 'react-router';
import headerBackground from '../../assets/cabecera_esi_fondo-1.png';
import esiLogo from '../../assets/LogoESI_cabecera-1-1.png';
import smartEsiBanner from '../../assets/smartesi-banner.webp';
import uclmLogo from '../../assets/logo_uclm.png';
import { RangeSelector } from './ui/RangeSelector';
import { useGlobalRange } from '../context/RangeContext';
import { DASHBOARD_TABS } from '../lib/sections';
import type { DashboardTabId } from '../lib/sections';
import { ENERGY_RANGES } from '../types/energy';
import { RANGE_LABEL } from '../lib/format';

const RANGE_OPTIONS = ENERGY_RANGES.map((range) => ({ value: range, label: RANGE_LABEL[range] }));

interface HeaderProps {
  activeTab: DashboardTabId;
  onSelectTab: (tab: DashboardTabId) => void;
}

export function Header({ activeTab, onSelectTab: onSelectTabProp }: HeaderProps) {
  const { range, setRange } = useGlobalRange();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white shadow-none">
      <div
        className="border-t-[5px] border-accent bg-white bg-right bg-no-repeat"
        style={{ backgroundImage: `url(${headerBackground})`, backgroundSize: 'auto 100%' }}
      >
        <div className="mx-auto flex min-h-28 max-w-7xl flex-col justify-center gap-4 px-4 py-5 sm:px-6 md:min-h-32 md:flex-row md:items-center md:justify-between lg:px-8">
          <Link to="/" className="flex min-w-0 items-center gap-4 sm:gap-5">
            <div className="flex shrink-0 flex-col items-start gap-2">
              <img
                src={uclmLogo}
                alt="Universidad de Castilla-La Mancha"
                className="h-10 w-auto sm:h-12"
              />
              <img
                src={esiLogo}
                alt="Escuela Superior de Informática"
                className="h-10 w-auto max-w-[12rem] object-contain object-left sm:h-12 sm:max-w-[16rem]"
              />
            </div>
          </Link>

          <div className="flex flex-col items-start gap-2 md:items-end">
            <div className="hidden max-w-sm border-l border-slate-200 bg-white/70 px-4 py-2 text-right text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 md:block">
              Estadísticas para la toma de decisiones
            </div>
            {activeTab !== 'electricidad' && (
              <div className="flex items-center gap-2 rounded-sm border border-slate-200 bg-white/90 px-3 py-2">
                <span className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Periodo
                </span>
                <RangeSelector
                  options={RANGE_OPTIONS}
                  value={range}
                  onChange={setRange}
                  ariaLabel="Periodo de todas las gráficas"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="border-b border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
          <div className="shrink-0 py-1.5">
            <div className="flex items-center">
              <h1 className="sr-only">Smart ESI · Estadísticas</h1>
              <img
                src={smartEsiBanner}
                alt="Smart ESI - Monitorización en tiempo real"
                className="h-12 w-auto max-w-full object-contain sm:h-14"
              />
            </div>
          </div>

          <nav
            className="flex min-w-0 flex-1 justify-end overflow-x-auto"
            aria-label="Pestañas del panel"
          >
            <div className="flex items-stretch border-l border-slate-200">
              {DASHBOARD_TABS.map((tab) => {
                const isActive = tab.id === activeTab;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => onSelectTabProp(tab.id)}
                    aria-pressed={isActive}
                    className={`relative flex shrink-0 cursor-pointer items-center border-r border-slate-200 px-5 py-5 text-sm font-semibold text-slate-800 transition-colors hover:text-primary ${
                      isActive ? 'text-primary' : ''
                    }`}
                  >
                    {tab.label}
                    {isActive && (
                      <motion.div
                        layoutId="headerActiveLine"
                        className="absolute inset-x-5 bottom-0 h-0.5 bg-accent"
                        initial={false}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                      />
                    )}
                  </button>
                );
              })}
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
}
