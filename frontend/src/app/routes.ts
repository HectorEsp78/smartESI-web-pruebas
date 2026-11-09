import { createBrowserRouter } from 'react-router';
import { Stats } from './pages/Stats';
import { NotFound } from './pages/NotFound';
import { RouteError } from './pages/RouteError';

const routerBasename =
  import.meta.env.BASE_URL === '/'
    ? undefined
    : import.meta.env.BASE_URL.replace(/\/$/, '');

const appRoutes = [
  {
    path: '/',
    Component: Stats,
    ErrorBoundary: RouteError,
  },
  {
    path: '/infraestructura',
    Component: Stats,
    ErrorBoundary: RouteError,
  },
  {
    path: '/infraestructura/:roomId',
    Component: Stats,
    ErrorBoundary: RouteError,
  },
  {
    path: '/mantenimiento',
    Component: Stats,
    ErrorBoundary: RouteError,
  },
  {
    path: '/mantenimiento/:groupId',
    Component: Stats,
    ErrorBoundary: RouteError,
  },
  {
    path: '*',
    Component: NotFound,
  },
];

export const router = createBrowserRouter(appRoutes, { basename: routerBasename });
