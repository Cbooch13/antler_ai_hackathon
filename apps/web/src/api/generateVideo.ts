import { fal } from '@fal-ai/client';
import type { Intake, GeneratedImage, GeneratedVideo } from '../types';

const FAL_KEY = import.meta.env.VITE_FAL_API_KEY as string | undefined;
const VIDEO_MODEL = 'fal-ai/kling-video/v1.6/standard/image-to-video';

function clipPrompt(label: string, intake: Intake): string {
  const style = intake.stylePreferences.join(', ') || 'warm modern';
  const isInterior = label.toLowerCase().includes('interior');
  if (isInterior) {
    return `Slow cinematic pan through a ${style} ${label.replace('Interior — ', '')} in an Austin Texas home, smooth steady camera, warm lighting, photorealistic`;
  }
  return `Slow cinematic pan across a ${style} ${intake.propertyType} home in Austin Texas, smooth steady camera, golden hour, photorealistic`;
}

function extractVideoUrl(result: unknown): string {
  const data = ((result as Record<string, unknown>)['data'] ?? result) as Record<string, unknown>;
  return (
    (data['video'] as Record<string, string>)?.['url'] ??
    (data['video_url'] as string) ??
    (data['url'] as string) ??
    ''
  );
}

export async function generateVideo(
  images: GeneratedImage[],
  intake: Intake
): Promise<GeneratedVideo> {
  if (!FAL_KEY) throw new Error('VITE_FAL_API_KEY is not set');
  fal.config({ credentials: FAL_KEY });

  const clips = await Promise.all(
    images.map(async ({ label, url: imageUrl }) => {
      const prompt = clipPrompt(label, intake);
      const result = await fal.run(VIDEO_MODEL, {
        input: { image_url: imageUrl, prompt, duration: '5' },
      });
      return { label, url: extractVideoUrl(result) };
    })
  );

  return { clips };
}
