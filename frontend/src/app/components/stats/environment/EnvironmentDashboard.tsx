import { useParams } from 'react-router';
import { EnvironmentIndex } from './EnvironmentIndex';
import { EnvironmentRoomPage } from './EnvironmentRoomPage';

/**
 * `/infraestructura` is the compact index and `/infraestructura/:roomId` is
 * the detail page for one confirmed room.
 */
export function EnvironmentDashboard() {
  const { roomId } = useParams<{ roomId: string }>();
  if (roomId) {
    return <EnvironmentRoomPage roomId={roomId} />;
  }
  return <EnvironmentIndex />;
}
