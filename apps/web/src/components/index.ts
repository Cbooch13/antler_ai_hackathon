export { Icon } from './Icon';
export { Btn } from './Btn';
export { Status } from './Status';
export { Banner } from './Banner';
export { Panel } from './Panel';
export { JsonView } from './JsonView';
export { LockedState } from './LockedState';
export { Skel } from './Skel';
export { IosFrame } from './IosFrame';
export { ImageGallery } from './ImageGallery';
export { VideoPlayer } from './VideoPlayer';

export const fmt = {
  money: (n: number) => '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 }),
  num: (n: number) => n.toLocaleString('en-US'),
};
