import { generateRandomProfileNickName } from "@/utils/generator";

export type AgeType = string;

export const PositionTypeOptions = [
  'bottom',
  'versBottom',
  'vers',
  'versTop',
  'top',
  'side',
  'blower',
  'blowie'
] as const;

export type PositionType = typeof PositionTypeOptions[number];

export const BodyTypeOptions = [
  'petite',
  'slim',
  'average',
  'fit',
  'muscular',
  'stocky',
  'chubby',
  'large'
] as const;

export type BodyType = typeof BodyTypeOptions[number];

export const SexualityTypeOptions = [
  'gay',
  'bisexual',
  'curious',
  'trans',
  'fluid'
] as const;

export type SexualityType = typeof SexualityTypeOptions[number];

export const HostingTypeOptions = [
  'hostAndTravel',
  'hostOnly',
  'travelOnly'
] as const;

export type HostingType = typeof HostingTypeOptions[number];

export const TravelDistanceTypeOptions = [
  'none',
  'block',
  'neighbourhood',
  'city',
  'metropolitan',
  'state'
] as const;

export type TravelDistanceType = typeof TravelDistanceTypeOptions[number];

export const EggplantSizeTypeOptions = [
  'small',
  'average',
  'large',
  'extraLarge',
  'gigantic'
] as const;

export type EggplantSizeType = typeof EggplantSizeTypeOptions[number];

export const PeachShapeTypeOptions = [
  'small',
  'average',
  'bubble',
  'solid',
  'large'
] as const;

export type PeachShapeType = typeof PeachShapeTypeOptions[number];

export const HealthPracticesTypeOptions = [
  'condoms',
  'bb',
  'condomsOrBb',
  'noPenetrations'
] as const;

export type HealthPracticesType = typeof HealthPracticesTypeOptions[number];

export const HivStatusTypeOptions = [
  'negative',
  'positive',
  'positiveUndetectable'
] as const;

export type HivStatusType = typeof HivStatusTypeOptions[number];

export const PreventionPracticesTypeOptions = [
  'none',
  'prep',
  'doxypep',
  'prepAndDoxypep'
] as const;

export type PreventionPracticesType = typeof PreventionPracticesTypeOptions[number];

export const MeetingTimeTypeOptions = [
  'now',
  'today',
  'whenever'
] as const;

export type MeetingTimeType = typeof MeetingTimeTypeOptions[number];

export const ChatStatusTypeOptions = [
  'online',
  'busy',
  'offline',
] as const;

export type ChatStatusType = typeof ChatStatusTypeOptions[number];

export interface ProfileImage {
  imageId: string;
  imageUrl: string;
  imageThumbnailUrl: string;
  imageAttributes: Record<string, string>;
}

export type ProfileId = string;

export interface ProfileRecord {
  profileId: ProfileId | null;
  nickName: string | undefined;
  aboutMe: string | undefined;
  age: AgeType | undefined;
  position: PositionType | undefined;
  body: BodyType | undefined;
  eggplantSize: EggplantSizeType | undefined;
  peachShape: PeachShapeType | undefined;
  healthPractices: HealthPracticesType | undefined;
  hivStatus: HivStatusType | undefined;
  preventionPractices: PreventionPracticesType | undefined;
  hosting: HostingType | undefined;
  travelDistance: TravelDistanceType | undefined;
  profileImages: ProfileImage[];
};

export interface SelfProfileRecord extends ProfileRecord {
  profileName: string | undefined;
};

export interface PeerProfileRecord extends ProfileRecord {
  distance: number;
  lastSeen: number;
};

export interface ProfileDB {
  activeProfileId: ProfileId;
  profileRecords: Record<ProfileId, SelfProfileRecord>;
  freeProfileIds: ProfileId[];
};

export const createProfileRecord = (locale: any, profileId: ProfileId, record: Partial<SelfProfileRecord> = {}): SelfProfileRecord => ({
  profileId: profileId,
  profileName: record?.profileName || locale.toString(locale.translations.globalDict.myProfile),
  nickName: record?.nickName || generateRandomProfileNickName(locale, profileId),
  aboutMe: record?.aboutMe,
  age: record?.age,
  position: record?.position,
  body: record?.body,
  eggplantSize: record?.eggplantSize,
  peachShape: record?.peachShape,
  healthPractices: record?.healthPractices,
  hivStatus: record?.hivStatus,
  preventionPractices: record?.preventionPractices,
  hosting: record?.hosting,
  travelDistance: record?.travelDistance,
  profileImages: record?.profileImages || [],
});
