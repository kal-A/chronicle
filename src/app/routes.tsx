import { createBrowserRouter } from 'react-router-dom'
import { AskEntryPage } from '../features/investigation/ask/AskEntryPage'
import { InvestigationPage } from '../features/investigation/InvestigationPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AskEntryPage />,
  },
  {
    path: '/investigations/:packageId/scenes/:sceneId',
    element: <InvestigationPage />,
  },
  {
    path: '/investigations/:packageId/scenes/:sceneId/inspector',
    element: <InvestigationPage mode="inspector" />,
  },
])
