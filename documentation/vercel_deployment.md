# Vercel Deployment

Vercel is a cloud platform for deploying static sites, serverless functions, and full-stack applications. It integrates seamlessly with Git and supports automated deployments.

## Key Features

* **Git Integration:** Connect your GitHub, GitLab, or Bitbucket repository for automatic deployments on every push.
* **Custom Domains & HTTPS:** Easily add custom domains with automatic SSL.
* **Serverless Functions:** Deploy backend logic as serverless functions alongside your frontend.
* **CLI & SDK:** Use the Vercel CLI or SDK for advanced deployment automation and scripting.

## Basic Deployment Workflow

1. **Push to Git:** Commit and push your code to your repository.
2. **Import Project:** Import your repo into Vercel via the dashboard or CLI.
3. **Configure:** Vercel auto-detects frameworks and build settings, but you can customize as needed.
4. **Deploy:** Vercel builds and deploys your app, providing a live URL.

## Advanced: Deploying with the Vercel SDK (TypeScript Example)

```typescript
import { VercelCore } from "@vercel/sdk/core.js";
import { deploymentsCreateDeployment } from "@vercel/sdk/funcs/deploymentsCreateDeployment.js";

const vercel = new VercelCore({ bearerToken: "<YOUR_BEARER_TOKEN>" });

async function deploy() {
  const res = await deploymentsCreateDeployment(vercel, {
    teamId: "<team_id>",
    slug: "<project_slug>",
    requestBody: {
      name: "my-deployment",
      project: "my-project",
      target: "production",
      // ...other config
    },
  });
  if (!res.ok) throw res.error;
  console.log(res.value);
}
```

## Further Reading
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel SDK Reference](https://vercel.com/docs/sdk)
- [Vercel CLI](https://vercel.com/docs/cli)
