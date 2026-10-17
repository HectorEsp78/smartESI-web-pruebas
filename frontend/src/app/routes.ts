import { createBrowserRouter } from 'react-router';
import { Stats } from './pages/Stats';
import { NotFound } from './pages/NotFound';

export const routerBasename =
  import.meta.env.BASE_URL === '/'
    ? undefined
    : import.meta.env.BASE_URL.replace(/\/$/, '');

export const appRoutes = [
  {
    path: '/',
    Component: Stats,
  },
  {
    path: '*',
    Component: NotFound,
  },
];

export const router = createBrowserRouter(appRoutes, { basename: routerBasename });
