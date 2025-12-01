import { baseUrl } from 'lib/utils';
import { MetadataRoute } from 'next';

export const dynamic = 'force-dynamic';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routes = [
    '',
    '/explorer',
    '/search',
  ].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date().toISOString(),
  }));

  return routes;
}
