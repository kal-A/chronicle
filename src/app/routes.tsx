import { createBrowserRouter, Navigate } from 'react-router-dom'
import { InvestigationPage } from '../features/investigation/InvestigationPage'
import { getDefaultInvestigationRoute } from '../features/investigation/data/investigationRepository'

const defaultRoute = getDefaultInvestigationRoute()
const defaultInvestigationPath = `/investigations/${encodeURIComponent(
  defaultRoute.packageId,
)}/scenes/${encodeURIComponent(defaultRoute.sceneId)}`

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to={defaultInvestigationPath} replace />,
  },
  {
    path: '/investigations/:packageId/scenes/:sceneId',
    element: <InvestigationPage />,
  },
])
