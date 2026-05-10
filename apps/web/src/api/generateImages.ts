import { fal } from '@fal-ai/client';
import type { Intake, FloorPlanEntry, LotGeometry, GeneratedImageSet } from '../types';

const FAL_KEY = import.meta.env.VITE_FAL_API_KEY as string | undefined;
const MODEL = 'fal-ai/flux/dev';

function styleStr(intake: Intake): string {
  return intake.stylePreferences.join(', ') || 'warm modern';
}

function lotDimStr(geo: LotGeometry | null, intake: Intake): string {
  const sqft = geo?.lotSqft ?? intake.lotSqft ?? 6500;
  const side = Math.round(Math.sqrt(sqft));
  return `${side}×${side} ft`;
}

function base(intake: Intake, plan: FloorPlanEntry): string {
  return `${styleStr(intake)} ${intake.propertyType} home, Austin Texas, ${plan.name} floor plan`;
}

function txt2img(prompt: string): Promise<string> {
  return fal
    .run(MODEL, { input: { prompt, num_inference_steps: 28, guidance_scale: 3.5, image_size: 'landscape_16_9' } })
    .then(extractUrl);
}

function extractUrl(result: unknown): string {
  const r = result as Record<string, unknown>;
  const d = (r['data'] ?? r) as Record<string, unknown>;
  const images = (d['images'] as unknown[] | undefined) ?? [];
  const img = images[0];
  return typeof img === 'string' ? img : (img as Record<string, string>)?.['url'] ?? '';
}

const SHOTS: { label: string; suffix: string }[] = [
  { label: 'Exterior — rear yard', suffix: 'rear yard view, outdoor patio, Texas native plants, afternoon light, photorealistic 8k' },
  { label: 'Interior — living & dining', suffix: 'interior living and dining room, open plan, natural light through large windows, warm tones, photorealistic 8k' },
  { label: 'Interior — kitchen', suffix: 'interior kitchen, modern cabinetry, quartz countertops, natural light, photorealistic 8k' },
  { label: 'Interior — primary bedroom', suffix: 'interior primary bedroom, serene, neutral palette, morning light, photorealistic 8k' },
  { label: 'Interior — bathroom', suffix: 'interior primary bathroom, walk-in shower, warm lighting, clean lines, photorealistic 8k' },
];

export async function generateImages(
  intake: Intake,
  plan: FloorPlanEntry,
  lotGeometry: LotGeometry | null
): Promise<GeneratedImageSet> {
  if (!FAL_KEY) throw new Error('VITE_FAL_API_KEY is not set');
  fal.config({ credentials: FAL_KEY });

  const b = base(intake, plan);
  const dims = lotDimStr(lotGeometry, intake);

  const extFrontPrompt = [
    b,
    `${dims} lot`,
    'professional architectural photography, golden hour sunlight',
    'wide angle street view, lush Texas landscaping',
    'photorealistic, 8k, sharp focus',
  ].join(', ');

  // Generate all images in parallel — each as its own txt2img call with a
  // distinct prompt so they look different from one another.
  const shotPrompts = SHOTS.map(({ suffix }) =>
    [b, suffix, 'professional photography, sharp focus'].join(', ')
  );

  const [extFrontUrl, ...restUrls] = await Promise.all([
    txt2img(extFrontPrompt),
    ...shotPrompts.map(txt2img),
  ]);

  return {
    images: [
      { label: 'Exterior — front street view', url: extFrontUrl, prompt: extFrontPrompt },
      ...SHOTS.map(({ label }, i) => ({ label, url: restUrls[i], prompt: shotPrompts[i] })),
    ],
    referenceImageUrl: extFrontUrl,
  };
}
