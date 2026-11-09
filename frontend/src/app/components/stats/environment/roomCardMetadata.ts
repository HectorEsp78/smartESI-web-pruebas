import a11Image from '../../../../assets/room-cards-images/A11-JohnVonNeumann.webp';
import a12Image from '../../../../assets/room-cards-images/A12-TimBernersLee.webp';
import a21Image from '../../../../assets/room-cards-images/A21-GeorgeBoole.webp';
import a22Image from '../../../../assets/room-cards-images/A22-GraceMurray.webp';

export interface RoomCardMetadata {
  technicalCode: string;
  personName: string;
  imageSrc: string;
  imageAlt: string;
}

const ROOM_CARD_METADATA: Record<string, RoomCardMetadata> = {
  A11: {
    technicalCode: 'A11',
    personName: 'John von Neumann',
    imageSrc: a11Image,
    imageAlt: 'Aula A11 · John von Neumann',
  },
  A12: {
    technicalCode: 'A12',
    personName: 'Tim Berners-Lee',
    imageSrc: a12Image,
    imageAlt: 'Aula A12 · Tim Berners-Lee',
  },
  A21: {
    technicalCode: 'A21',
    personName: 'George Boole',
    imageSrc: a21Image,
    imageAlt: 'Aula A21 · George Boole',
  },
  A22: {
    technicalCode: 'A22',
    personName: 'Grace Murray Hopper',
    imageSrc: a22Image,
    imageAlt: 'Aula A22 · Grace Murray Hopper',
  },
};

/** Rooms shown in the first version of the Infrastructure tab. */
export const INFRASTRUCTURE_ROOM_IDS = ['A11', 'A12', 'A21', 'A22'] as const;

export function getRoomCardMetadata(roomId: string): RoomCardMetadata | null {
  return ROOM_CARD_METADATA[roomId] ?? null;
}
