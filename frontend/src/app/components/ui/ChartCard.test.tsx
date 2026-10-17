import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ChartCard } from './ChartCard';

const baseProps = {
  title: 'Título',
  subtitle: 'Subtítulo',
  isLoading: false,
  error: null as Error | null,
  onRetry: vi.fn(),
  children: <div>contenido</div>,
};

describe('ChartCard', () => {
  it('renders its children when there is data', () => {
    render(<ChartCard {...baseProps} />);
    expect(screen.getByText('contenido')).toBeInTheDocument();
  });

  it('shows a retry button on error', () => {
    render(<ChartCard {...baseProps} error={new Error('boom')} />);
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
  });

  it('shows the empty message', () => {
    render(<ChartCard {...baseProps} isEmpty emptyMessage="sin datos" />);
    expect(screen.getByText('sin datos')).toBeInTheDocument();
  });
});
