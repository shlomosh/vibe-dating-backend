import { generateRandomProfileNickName } from "@/utils/generator";

/**
 * User Profile Type Definitions for Vibe Dating App
 * 
 * This file contains comprehensive TypeScript type definitions for user profiles,
 * including all profile attributes, enums, and data structures used in the frontend.
 * 
 * @author Vibe Dating Backend Team
 * @version 1.0.0
 */

/**
 * Represents a user's age as a string value
 */
export type AgeType = string;

/**
 * Available sexual position preferences for user profiles
 */
export const SexualPositionTypeOptions = [
  'bottom',
  'versBottom',
  'vers',
  'versTop',
  'top',
  'side',
  'blower',
  'blowie'
] as const;

/**
 * Type representing a user's sexual position preference
 */
export type SexualPositionType = typeof SexualPositionTypeOptions[number];

/**
 * Available body type classifications for user profiles
 */
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

/**
 * Type representing a user's body type
 */
export type BodyType = typeof BodyTypeOptions[number];

/**
 * Available sexuality classifications for user profiles
 */
export const SexualityTypeOptions = [
  'gay',
  'bisexual',
  'curious',
  'trans',
  'fluid'
] as const;

/**
 * Type representing a user's sexuality
 */
export type SexualityType = typeof SexualityTypeOptions[number];

/**
 * Available hosting preferences for meetups
 */
export const HostingTypeOptions = [
  'hostAndTravel',
  'hostOnly',
  'travelOnly'
] as const;

/**
 * Type representing a user's hosting preference
 */
export type HostingType = typeof HostingTypeOptions[number];

/**
 * Available travel distance preferences for meetups
 */
export const TravelDistanceTypeOptions = [
  'none',
  'block',
  'neighbourhood',
  'city',
  'metropolitan',
  'state'
] as const;

/**
 * Type representing how far a user is willing to travel
 */
export type TravelDistanceType = typeof TravelDistanceTypeOptions[number];

/**
 * Available anatomy size classifications
 */
export const EggplantSizeTypeOptions = [
  'small',
  'average',
  'large',
  'extraLarge',
  'gigantic'
] as const;

/**
 * Type representing anatomy size preference
 */
export type EggplantSizeType = typeof EggplantSizeTypeOptions[number];

/**
 * Available anatomy shape classifications
 */
export const PeachShapeTypeOptions = [
  'small',
  'average',
  'bubble',
  'solid',
  'large'
] as const;

/**
 * Type representing anatomy shape preference
 */
export type PeachShapeType = typeof PeachShapeTypeOptions[number];

/**
 * Available health practice preferences for safe encounters
 */
export const HealthPracticesTypeOptions = [
  'condoms',
  'bb',
  'condomsOrBb',
  'noPenetrations'
] as const;

/**
 * Type representing a user's health practice preferences
 */
export type HealthPracticesType = typeof HealthPracticesTypeOptions[number];

/**
 * Available HIV status classifications
 */
export const HivStatusTypeOptions = [
  'negative',
  'positive',
  'positiveUndetectable'
] as const;

/**
 * Type representing a user's HIV status
 */
export type HivStatusType = typeof HivStatusTypeOptions[number];

/**
 * Available prevention practice options for sexual health
 */
export const PreventionPracticesTypeOptions = [
  'none',
  'prep',
  'doxypep',
  'prepAndDoxypep'
] as const;

/**
 * Type representing a user's prevention practices
 */
export type PreventionPracticesType = typeof PreventionPracticesTypeOptions[number];

/**
 * Available meeting time preferences
 */
export const MeetingTimeTypeOptions = [
  'now',
  'today',
  'whenever'
] as const;

/**
 * Type representing when a user is available to meet
 */
export type MeetingTimeType = typeof MeetingTimeTypeOptions[number];

/**
 * Available chat status options for real-time communication
 */
export const ChatStatusTypeOptions = [
  'online',
  'busy',
  'offline',
] as const;

/**
 * Type representing a user's current chat availability
 */
export type ChatStatusType = typeof ChatStatusTypeOptions[number];

/**
 * Represents a profile image with metadata
 */
export interface ProfileImage {
  /** Unique identifier for the image */
  imageId: string;
  /** Full resolution image URL */
  imageUrl: string;
  /** Thumbnail image URL for previews */
  imageThumbnailUrl: string;
  /** Additional image metadata and attributes */
  imageAttributes: Record<string, string>;
}

/**
 * Unique identifier for a user profile
 */
export type ProfileId = string;

/**
 * Base interface for all profile records containing common profile data
 */
export interface ProfileRecord {
  /** Unique profile identifier */
  profileId: ProfileId | null;
  /** User's display nickname */
  nickName: string | undefined;
  /** User's profile description */
  aboutMe: string | undefined;
  /** User's age */
  age: AgeType | undefined;
  /** User's sexual position preference */
  sexualPosition: SexualPositionType | undefined;
  /** User's body type */
  bodyType: BodyType | undefined;
  /** User's anatomy size preference */
  eggplantSize: EggplantSizeType | undefined;
  /** User's anatomy shape preference */
  peachShape: PeachShapeType | undefined;
  /** User's health practices */
  healthPractices: HealthPracticesType | undefined;
  /** User's HIV status */
  hivStatus: HivStatusType | undefined;
  /** User's prevention practices */
  preventionPractices: PreventionPracticesType | undefined;
  /** User's hosting preferences */
  hosting: HostingType | undefined;
  /** User's travel distance preference */
  travelDistance: TravelDistanceType | undefined;
  /** Array of profile images */
  profileImages: ProfileImage[];
};

/**
 * Extended profile record for the current user's own profile
 */
export interface SelfProfileRecord extends ProfileRecord {
  /** Internal profile name for organization */
  profileName: string | undefined;
};

/**
 * Extended profile record for other users' profiles with additional metadata
 */
export interface PeerProfileRecord extends ProfileRecord {
  /** Distance from current user in kilometers */
  distance: number;
  /** Timestamp of when user was last seen online */
  lastSeen: number;
};

/**
 * Database structure for managing user profiles locally
 */
export interface ProfileDB {
  /** Currently active profile ID */
  activeProfileId: ProfileId;
  /** Map of profile IDs to profile records */
  profileRecords: Record<ProfileId, SelfProfileRecord>;
  /** Array of available profile IDs for new profiles */
  freeProfileIds: ProfileId[];
};

/**
 * Factory function to create a new profile record with default values
 * 
 * @param locale - Localization object for translations
 * @param profileId - Unique identifier for the new profile
 * @param record - Partial profile data to override defaults
 * @returns Complete SelfProfileRecord with defaults applied
 */
export const createProfileRecord = (locale: any, profileId: ProfileId, record: Partial<SelfProfileRecord> = {}): SelfProfileRecord => ({
  profileId: profileId,
  profileName: record?.profileName || locale.toString(locale.translations.globalDict.myProfile),
  nickName: record?.nickName || generateRandomProfileNickName(locale, profileId),
  aboutMe: record?.aboutMe,
  age: record?.age,
  sexualPosition: record?.sexualPosition,
  bodyType: record?.bodyType,
  eggplantSize: record?.eggplantSize,
  peachShape: record?.peachShape,
  healthPractices: record?.healthPractices,
  hivStatus: record?.hivStatus,
  preventionPractices: record?.preventionPractices,
  hosting: record?.hosting,
  travelDistance: record?.travelDistance,
  profileImages: record?.profileImages || [],
});
