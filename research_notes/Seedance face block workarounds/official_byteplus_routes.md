# Official ByteDance / BytePlus / Volcengine routes for photoreal faces in Seedance 2.0 / 2.5

> **Method note (read first).** The egress proxy in this research session refused connections to docs.byteplus.com, ai.byteplus.com, docs.volcengine.com and every other non-GitHub site (`connect_rejected`), so WebFetch could not open the official pages. The evidence comes from:
> (a) search-engine summaries and quoted snippets of the official pages (docs.byteplus.com/en/docs/ModelArk/2333565, /2333589, /2315856, /2608626, /2275639; docs.volcengine.com ark guides);
> (b) **byteplus-sa/ark-mcp**, a ByteDance-collaborator repo whose PR #74 was authored by `ArthurReimus-ByteDance` and merged 2026-09-24. I cloned it and read `docs/assets.md`, `specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md`, `plans/PLAN_MODELARK_ASSET_LIBRARY.md` and `plans/PLAN_MODELARK_ASSET_LIBRARY_VALIDATION.md`. These files cite the official doc IDs (2333565, 2333589, 2315856, 2318271 CreateAsset, 2318278, 2377608 rights purchase, 2548867 copyright IP) as accessed 2026-09-23, and they record live provider tests;
> (c) **moku-labs/ai PR #15**, a third-party Node/TypeScript implementation. I read its `src/plugins/ark/README.md`, `regions.ts` and `sign.ts`.
>
> Third-party blogs (seedrouter, reapi, yingtu, clipdance, vicsee and others) appear only where they quote official text, and are flagged as secondhand. Treat any exact wording attributed to the official docs as "quoted via search snippet" until someone checks it in a browser.

---

## 1. What the ModelArk docs say about real-human faces, why the block exists, and whether AI-generated faces are treated differently

### Takeaway
ModelArk's input rule is categorical: Seedance 2.0 and 2.5 do not accept directly uploaded reference images or videos that contain real human faces. A classifier enforces it, returning HTTP 400 `InputImageSensitiveContentDetected.PrivacyInformation`. The classifier does not reliably tell a photoreal AI-generated face from a real one: in practice "looks real" equals "blocked". The docs exempt only faces that arrive through trusted channels: (1) the asset library (virtual portraits, verified real humans, preset avatars, copyright IP); (2) the account's own original Seedream/Seedance outputs within 30 days.

### Cited Findings
- Official line (quoted via search snippets): "Seedance 2.5 and Seedance 2.0 series models do not support directly uploading reference images/videos that contain real human faces." — [seedrouter.ai summary quoting ModelArk](https://seedrouter.ai/blog/seedance-real-person-error); [yingtu.ai](https://yingtu.ai/en/blog/seedance-2-0-human-face)
- The error code is listed in ModelArk's error-code list as an HTTP 400; ModelArk defines two such sensitive-input codes, and resending the same file reproduces the error. — [yingtu.ai](https://yingtu.ai/en/blog/seedance-2-0-human-face); [seedrouter.ai](https://seedrouter.ai/blog/seedance-real-person-error)
- The Volcengine docs (summarised in Chinese search results) describe Seedance 2.0 as having a built-in anti-deepfake and anti-infringement block ("内置防 Deepfake / 侵权拦截") that refuses reference images containing real faces. Even virtual characters are advised to go through the private asset library first. — [Volcengine 私域虚拟人像素材资产库使用指南](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview); [API易 doc](https://docs.apiyi.com/api-capabilities/seedance2/asset-library)
- Official BytePlus docs state that "risky reference material input will be intercepted during video generation", which is why portraits go through the library rather than as raw photos. — [ModelArk 2333565 (search snippet)](https://docs.byteplus.com/en/docs/ModelArk/2333565)
- Official docs on the digital-character route say virtual (digital) characters are for "scenarios that require real-human-style faces but do not need to specify a particular person". A real, specific person needs a separate consent and authorization workflow. — [search summary of ModelArk docs](https://docs.byteplus.com/en/docs/ModelArk/2608626)
- **AI-generated faces are not exempt by default.** A developer issue reports that a photoreal *fictional* (AI-generated) character sheet was refused with `InputImageSensitiveContentDetected.PrivacyInformation`. — [openstory issue #1927](https://github.com/openstory-so/openstory/issues/1927). A Volcengine-user issue reports the same for an AI-generated realistic person used as a reference or first frame, and asks for `asset://` portrait-library support as the fix. — [ArcReel issue #2249](https://github.com/ArcReel/ArcReel/issues/2249). ComfyUI changed its website copy to tell users that Seedance blocks realistic faces even when they are AI-generated. — [ComfyUI_frontend PR #19638](https://github.com/Comfy-Org/ComfyUI_frontend/pull/19638)
- The error "does not prove the image actually shows a real person"; the classifier can treat a synthetic face as possibly real. — [yingtu.ai](https://yingtu.ai/en/blog/seedance-2-0-human-face)
- A third-party implementation documents the behaviour: "Ark refuses a plain photo that may show a real person (`InputImageSensitiveContentDetected.*`)… There is no raw-photo fallback… A refused task is not billed." Its remedy is to register the portrait as an asset first. — [moku-labs/ai PR #15, src/plugins/ark/README.md](https://github.com/moku-labs/ai/pull/15)
- The asset-library terms define the library as covering "pre-set virtual avatars, templates, and other similar items provided by Byteplus", custom uploads, and "portraits or voice assets of natural persons for which you have obtained authorization". — [Byteplus Terms of Use for Asset Library, 2275639](https://docs.byteplus.com/en/docs/ModelArk/2275639)
- Evasion techniques circulate: character-sheet grids, overlays and noise, for example in [ViralTwin "character-sheet trick"](https://www.viraltwin.app/blog/pass-seedance-face-filter) and [vicsee](https://vicsee.com/blog/seedance-content-filter). These are third-party, not official, and aim to defeat a likeness-protection control. Not researched further.

### Inferences
- In practice the classifier separates "photoreal human face" from "stylised, cartoon or 3D face", not "real" from "AI-generated". A photoreal AI character should be treated as blocked for raw upload and routed through the AIGC virtual-portrait library (Section 2) or the trusted-output route (Section 4).
- The policy's purpose (deepfake, privacy and likeness protection) explains the shape of the exemptions: every one of them ties the face to provenance, either a consenting verified person, a declared-fictional AIGC asset under a signed authorization letter, or the platform's own output.

### Gaps
- I could not read the exact official page wording, or confirm whether ModelArk's error list names the second sensitive-input code (likely a non-privacy `InputImageSensitiveContentDetected` variant).
- No official statement found on whether 2.5 moderates more or less strictly than 2.0. Sources treat the rule as identical for both series.

---

## 2. Private virtual portrait library (AIGC): creation, auth, review, status, `asset://`, request usage, regions, costs, eligibility

### Takeaway
1. Create an **AIGC asset group**, one per fictional character, with signed OpenAPI calls (AK/SK, HMAC-SHA256). The first time, sign an authorization letter in the console.
2. `CreateAsset` from a **public HTTPS URL**, one per call, no base64. The call is asynchronous.
3. Poll `GetAsset` until `Status` = `Active`.
4. Reference the asset as `asset://<asset_id>` in the Seedance `content[].image_url.url`, normally with `role: "reference_image"`. The **generation** call needs only the normal Bearer API key.
5. The feature requires **Dreamina Seedance Advanced Creation Rights**. The free "Advanced Entry" tier already allows API access, with a 50-asset / 50-group cap and 3 `CreateAsset` calls per minute.

### Cited Findings
**Concepts and console**
- Asset group = one subject (a person, character or product). Asset = one image, video or audio file, with an ID like `asset-20260318035710-kctzf`. `AIGC` groups appear under the console's *Virtual Portrait* tab, are created by API, and "must **not** resemble any real person". — [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md)
- Official: "When creating an asset group for the first time, you must sign an authorization letter in the console." Uploaded portraits can be viewed at "ModelArk Console > My assets > Virtual Portrait". — [ModelArk 2333565 (search snippet)](https://docs.byteplus.com/en/docs/ModelArk/2333565)
- Official: "Only the Asset ID of assets already added to the library can be used for video generation". After creating an asset, "you can use the asset Id (must be in active status) returned in the response fields"; "You can use the GetAsset API to view whether the upload was successful." — [ModelArk 2333565 (search snippet)](https://docs.byteplus.com/en/docs/ModelArk/2333565)
- BytePlus help-centre FAQ: "upload it to the Asset Library to obtain an asset ID, then pass that asset ID (not a raw image URL) when calling the model". The asset's access URL expires, "but the asset ID itself remains valid for generation." — [ai.byteplus.com help article](https://ai.byteplus.com/en/help/article/how-do-i-use-reference-images-virtual-characters-and-the-asset-library-correctly)

**Auth (two different credentials)**
- Asset **management** uses BytePlus IAM AK/SK, which is separate from the ModelArk API key. The IAM user needs `ArkFullAccess` on the ModelArk project. **Using** assets in Seedance needs only the normal API key; `asset://` references work without AK/SK, for example for assets created in the console. — [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md)
- "The asset docs state that the Assets API requires Access Key authentication. An API key cannot create groups or upload assets." — [ark-mcp validation plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY_VALIDATION.md)
- Signing: BytePlus OpenAPI V4 HMAC-SHA256, service `ark`, region `ap-southeast-1`, Version `2024-01-01`, host `ark.ap-southeast-1.byteplusapi.com`. STS temporary keys (`AKTP…`) need `X-Security-Token` in the signed headers. Errors come back in a `ResponseMetadata.Error` envelope, for example `InvalidAccessKey` (100009) and `InvalidSecretToken` (100026). — [ark-mcp SPEC](https://github.com/byteplus-sa/ark-mcp/blob/main/specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md)
- Node.js signer details (third-party, working implementation):
  - Request: `POST https://<host>/?Action=<Action>&Version=2024-01-01` with a JSON body.
  - Signed headers: `content-type;host;x-content-sha256;x-date`.
  - Signing key: `HMAC(HMAC(HMAC(HMAC(secret, yyyymmdd), region), "ark"), "request")`.
  - Header format: `Authorization: HMAC-SHA256 Credential=AK/<date>/<region>/ark/request, SignedHeaders=..., Signature=<hex>`.
  - [moku-labs/ai PR #15 sign.ts](https://github.com/moku-labs/ai/pull/15)

**Live-verified OpenAPI actions** (AIGC path, 2026-09-24, `default` project)

| Action | Request fields | Observed |
|---|---|---|
| `ListAssetGroups` | `Filter: {GroupType:"AIGC"}`, `MaxResults`, `ProjectName` | `Result.Items`, `Result.NextToken`. Omitting `Filter` returns `MissingParameter.Filter` |
| `CreateAssetGroup` | `Name`, `Description`, `GroupType:"AIGC"`, `ProjectName` | `Result.Id` (e.g. `group-20260924075329-67prc`) |
| `GetAssetGroup` / `UpdateAssetGroup` | `Id`, `ProjectName` (+ `Description`) | ok |
| `CreateAsset` | `GroupId`, public HTTPS `URL`, `AssetType:"Image"`, `Name`, `ProjectName` | `Result.Id` (e.g. `asset-20260924075358-s9g98`) |
| `GetAsset` | `Id`, `ProjectName` | `Result.Status` → `Active`; also `GroupId`, `AssetType`, `Name`, `Moderation`, timestamps, temporary `URL` |
| `ListAssets` | `Filter:{GroupType:"AIGC", GroupIds:[…]}`, `MaxResults`, `ProjectName` | ok |
| `UpdateAsset` | `Id`, `Name`, `ProjectName` | ok |
| `DeleteAsset` / `DeleteAssetGroup` | `Id`, `ProjectName` | irreversible; deleting a group removes its assets; then 404 `NotFound.asset_id` / `NotFound.group_id` |

Source: [ark-mcp SPEC](https://github.com/byteplus-sa/ark-mcp/blob/main/specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md)

**Review, status and timing**
- Official: the CreateAsset API "is asynchronous. System processing may result in queuing… higher latency is expected for uploading video. SLA for uploading time is not guaranteed." — [ModelArk 2333565 (search snippet)](https://docs.byteplus.com/en/docs/ModelArk/2333565)
- Statuses: `Processing`, then `Active` (usable) or `Failed`. In the live probe a synthetic cartoon image was `Active` on the first poll. `Failed` comes with a `FailedReason`. — [ark-mcp SPEC/validation](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY_VALIDATION.md); [moku-labs README](https://github.com/moku-labs/ai/pull/15)
- Volcengine docs: only assets with Status=Active can be used for video generation, and a successful CreateAsset response does not mean review has finished. — [Volcengine guide](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview) (via search summary)
- `GetAsset`'s `URL` is a presigned TOS link that expires after about 12 hours. Store only `asset://<id>`. — [ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md)

**File limits**

| Type | Formats | Limits |
|---|---|---|
| Image | jpeg, png, webp, bmp, tiff, gif, heic/heif | W/H ratio 0.4–2.5; each side 300–6000 px; < 30 MB |
| Video | mp4, mov | 2–30 s; 24–60 fps; each side 300–6000 px; total pixels 407,696–8,295,044; ≤ 200 MB |
| Audio | wav, mp3 | 2–30 s; ≤ 15 MB |

One public URL per `CreateAsset` call; base64 is not accepted. — [ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md)

**Recommended inputs**
- "clearly fictional images of the character: a front-facing close-up and a full-body shot, portrait orientation", all in the same group. — [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md)
- Do not put asset IDs in prompts. Refer to assets as "Image 1", "Image 2" by their position in the request (Volcengine: "图片1", "视频1"). — [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md); [Volcengine create-video-generation-task](https://docs.volcengine.com/docs/ark/create-video-generation-task-api) (via search summary)

**Using the asset in generation**
- Live-verified: Seedance 2.5 accepted `content[].image_url.url = "asset://<asset-id>"` with `role = "reference_image"` (model `dreamina-seedance-2-5-260628`, 480p, 9:16, 4 s).
- Native `asset://` support is not universal. Seedream 5.0 Pro returned HTTP 400 `InvalidParameter`, and Seed Audio returned HTTP 400 code `45001132`.
- Video and audio `asset://` references, and Seedance 2.0, are documented as supported but were not live-verified by ark-mcp.
- Source: [ark-mcp SPEC](https://github.com/byteplus-sa/ark-mcp/blob/main/specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md)
- `asset://` refs can also go in `first_frame` / `last_frame` image roles in some third-party implementations: moku maps plain images to `first_frame` and asset refs to `reference_image`. The Volcengine official example uses `reference_image`. — [moku-labs README](https://github.com/moku-labs/ai/pull/15); [Volcengine create task API (search summary)](https://docs.volcengine.com/docs/ark/create-video-generation-task-api)

**Eligibility, tiers, cost, project and region**
- The library comes with **Dreamina Seedance Advanced Creation Rights**. Official: "To access the full features of the Asset Library, you need to activate the Advanced Creation Rights. The capacity quota is shared between Private Virtual Avatar Asset Library and Real-human Portrait Library." — [ModelArk 2333565 (search snippet)](https://docs.byteplus.com/en/docs/ModelArk/2333565)
- Rights tiers (from purchase guide 2377608, via the ark-mcp plan):

  | Tier | API access | Assets / groups | `CreateAsset` rate |
  |---|---|---|---|
  | Basic (free) | console only | 50 / 50 | 3 QPM |
  | Advanced Entry (free) | API | 50 / 50 | 3 QPM |
  | Advanced ($1,400/mo) | API | 1M / 1M | 120 QPM |
  | Advanced Premium ($4,200/mo) | API | 5M / 5M | 300 QPM |

  Other rate limits: `GetAsset` 100 QPS; `DeleteAssetGroup` 5 QPS; `CreateVisualValidateSession` and `GetVisualValidateResult` 3 QPS; all other calls 10 QPS. — [ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md)
- When a paid tier lapses there is a 15-day grace period: existing assets still work, but no new assets or groups can be created. After that, "assets and groups created during the paid period are **deleted permanently**." — [ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md)
- Asset creation has no per-asset fee in the implementations seen ("the asset fee is part of the entitlement"). Video generation is billed normally. — [moku-labs README](https://github.com/moku-labs/ai/pull/15)
- Assets live in one `ProjectName` (default `default`) and work only with inference endpoints in the same project. An asset ID works only in the account that created it. — [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md); [moku-labs README](https://github.com/moku-labs/ai/pull/15)
- Error hints: without the entitlement, asset calls fail with `AccessDenied*` / `InvalidAuthorization*`, and a full quota returns `QuotaExceeded`. — [moku-labs README](https://github.com/moku-labs/ai/pull/15)

### Inferences
- For a moodboard app with AI-generated photoreal characters, the minimum compliant pipeline is:
  1. Activate Advanced Creation Rights (Entry tier is enough to start).
  2. Sign the authorization letter once in the console.
  3. Create an IAM AK/SK with `ArkFullAccess`.
  4. Host each character image at a public HTTPS URL; a short-lived presigned URL works.
  5. Call `CreateAssetGroup` (once per character), then `CreateAsset`.
  6. Poll `GetAsset` until `Active`.
  7. Call Seedance with `asset://`.
- The Entry tier's 50-asset cap and 3 QPM are the practical constraints.
- Because the AIGC group "must not resemble any real person", uploading a real person's photo here likely violates the terms and/or fails review.
- It is not clear whether `Active` means human review or only automated moderation. The `Moderation` field in `GetAsset` suggests automated screening.

### Gaps
- Exact human-review duration and criteria: "no SLA" is all that is documented.
- The exact console UI path for creating virtual portraits in Model Playground (beyond "My assets > Virtual Portrait"), and the purchase flow for the tiers. Not confirmed from primary pages.
- Whether `asset://` is officially accepted in `first_frame` / `last_frame` roles (as opposed to `reference_image`) in 2.0 and 2.5. Not confirmed officially. ark-mcp's tool schema allows `first_frame`, `last_frame` and `reference_image` for image items, but its live test covered only `reference_image`.
- Doc 2608626's page title is "Create portrait videos with Dreamina Seedance models"; I could not read its contents.

---

## 3. Private real-human asset library (invited users): liveness, `groupId`, consent

### Takeaway
A real person can be used only after they verify themselves:
1. Your backend calls `CreateVisualValidateSession` (AK/SK signed), which returns an H5 link and a token.
2. The person opens the H5 link, consents, and completes a liveness check.
3. `GetVisualValidateResult` returns a `LivenessFace` group ID.
4. Every `CreateAsset` into that group is face-matched against the verified person, and mismatched faces are rejected.

There is also a console QR flow that lets a person authorize their likeness to another account. The API guide is labelled "invited users only".

### Cited Findings
- Doc 2333589 is titled "Private real-human asset library guide (invited users only)". Doc 2315856 is "Add real-human assets to asset library". — [BytePlus doc index via search](https://docs.byteplus.com/en/docs/ModelArk/2333589); [2315856](https://docs.byteplus.com/en/docs/ModelArk/2315856)
- Flow:
  - `CreateVisualValidateSession` (`CallbackURL`, `ProjectName`) returns `BytedToken` and `H5Link`.
  - The person completes the liveness check plus consent.
  - `GetVisualValidateResult` (`BytedToken`, valid for about 30 minutes, plus `ProjectName`) returns `GroupId` (type `LivenessFace`).
  - `CreateAsset` into that group is face-matched, and uploads that do not match are rejected.
  - Send the H5 link **only** to the person being verified. It embeds temporary credentials.
  - Source: [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md); [ark-mcp SPEC](https://github.com/byteplus-sa/ark-mcp/blob/main/specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md)
- `LivenessFace` groups "cannot be created by name; they come only from a verification". Official: "Uploading materials of different individuals to the same material group is not supported." — [ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md)
- Real-human assets that another account authorizes to you through the console QR flow can be used by ID in Seedance, but the management APIs cannot query, update or delete them. — [ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md)
- Volcengine (CN): when an asset is added, the system compares its facial features against the reference image captured during real-person verification, and the asset is accepted only if they match. The person completes verification and authorization on mobile, and the user must hold that authorization before generating video. Each Asset Group corresponds to one real person. — [录入真人形象素材](https://docs.volcengine.com/docs/ark/upload-real-person-portrait-assets); [私域真人人像素材资产使用指南](https://docs.volcengine.com/docs/ark/guide-preview?lang=zh) (via search summary)
- A ComfyUI guide describes the same output: after the liveness check you get a group ID for the person and an asset ID per image. — [blog.comfy.org](https://blog.comfy.org/p/unlock-seedance20-real-human-video-generation)
- The real-human path is **not live-verified** in ark-mcp ("Real-human verification remains untested"). — [ark-mcp PR #74](https://github.com/byteplus-sa/ark-mcp/pull/74)
- The capacity quota is shared with the virtual-portrait library. — [ModelArk 2333565 (search snippet)](https://docs.byteplus.com/en/docs/ModelArk/2333565)

### Inferences
- This route fits real models, actors or the user themselves. It does not apply to fictional AI characters, which have no living person to pass a liveness check.

### Gaps
- What "invited users only" means operationally (application form, account manager) is not documented in what I could reach.
- The response shape of `GetVisualValidateResult` while verification is still pending is unknown.
- Whether consent can be revoked, and what happens to the assets if it is.

---

## 4. Trusted ModelArk outputs (reusing Seedream / Seedance outputs as face inputs)

### Takeaway
The docs (as quoted by several secondary sources) describe a trusted-output exemption. Original, unedited, face-containing outputs generated in the same account by Seedance 2.5 or 2.0 (videos and their last frames) or by Seedream 5.0 lite text-to-image can be fed back into Seedance 2.0 or 2.5 for 30 days without triggering input moderation. Edited, cross-account or expired outputs do not qualify.

### Cited Findings
- Quoted official text: "The original face-containing outputs generated by certain models under this account can be used as input assets to call Seedance 2.5 and Seedance 2.0 series models again for secondary creation, without triggering input moderation blocking." — [via search summary of clipdance/reapi/seedrouter quoting ModelArk](https://clipdance.ai/blog/seedance-2-real-face-workaround)
- Covered outputs: face-containing videos from Seedance 2.5 and the 2.0 series, their last frames, and Seedream 5.0 lite text-to-image images, for 30 days after generation. — [same](https://reapi.ai/blog/seedance-not-eligible-explained)
- Quoted: "Only original model outputs are trusted; they cannot be used after secondary editing or after the validity period has expired." Only outputs from the same account are trusted, and cross-account use is not supported. — [reapi.ai](https://reapi.ai/blog/seedance-not-eligible-explained); [yingtu.ai](https://yingtu.ai/en/blog/seedance-2-0-human-face)
- The ark-mcp plan lists "Seedream `save_to_asset_group` output ingestion" as not yet built. This suggests Seedream has an option to save outputs straight into an asset group. — [ark-mcp PR #74](https://github.com/byteplus-sa/ark-mcp/pull/74)

### Inferences
- Pass the original output URL (or last-frame URL) unchanged. Re-encoding, cropping, upscaling or compositing the image almost certainly breaks the trust match, probably a hash or provenance check.
- Output URLs expire after 24 hours (Seedance `video_url`), so re-upload may be needed. Whether a re-hosted byte-identical copy is still trusted is unknown.
- For a moodboard app this is the cheapest route: generate the character with Seedream 5.0 lite in the same ModelArk account, then use that untouched image as the Seedance `first_frame` within 30 days. Avoid any edits.

### Gaps
- I could not read the primary page for this rule, so the exact model list (for example whether Seedream 5.0 Pro or 4.x outputs count) is unconfirmed.
- The mechanism (URL, hash or watermark matching) is not documented.

---

## 5. Preset virtual avatars

### Takeaway
BytePlus provides a library of preset virtual avatars, platform-curated and pre-cleared fictional people, browsable in the console. They are referenced by asset ID as `asset://<id>` like any other asset, and BytePlus's own Asset Library terms govern their use.

### Cited Findings
- Terms: "Asset Library refers to pre-set virtual avatars, templates, and other similar items provided by Byteplus." The terms include separate rules "When you use the Reference Assets provided by Byteplus, such as those available in the virtual avatar library". — [2275639](https://docs.byteplus.com/en/docs/ModelArk/2275639)
- Referenced as `asset://<ASSET_ID>`. "The asset library is browsable from the studio interface; the IDs are visible there." — [clipdance.ai (third-party)](https://clipdance.ai/blog/seedance-2-real-face-workaround)
- Volcengine has a 虚拟人像库 (virtual portrait library) page. — [docs.volcengine.com/docs/ark/avatar-library](https://docs.volcengine.com/docs/ark/avatar-library?lang=zh)
- Copyright IP (separate console tab, *Copyright Library*): accept the IP's terms in the console, copy the asset ID, and use `asset://<id>`. There is no API for listing these. CJ7 content is billed at 1.1× the video price. — [ark-mcp docs/assets.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md)

### Gaps
- I could not find a list of the preset avatars, their count, or any official API for enumerating them. Whether they require Advanced Creation Rights is unconfirmed.

---

## 6. Volcengine (China) equivalents

### Takeaway
The China product (火山方舟 / Volcengine Ark) works the same way: 私域虚拟人像素材资产库, 私域真人人像素材资产, `asset://`, and `role: reference_image`. It differs in hosts, signing region and model-ID prefixes (`doubao-` instead of `dreamina-`).

### Cited Findings
- Official Volcengine pages: 私域虚拟人像素材资产库使用指南, 私域真人人像素材资产使用指南, 录入真人形象素材, 创建视频生成任务, 虚拟人像库. Their content as summarised by search matches BytePlus (Active-only usage, `asset://`, `reference_image`, face matching for real people, one person per group). — [docs.volcengine.com](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview)
- Hosts:

  | Region | Data plane (video, Bearer key) | Control plane (assets, signed) | Sign region | Currency |
  |---|---|---|---|---|
  | `intl` (BytePlus ModelArk) | `https://ark.ap-southeast.bytepluses.com/api/v3` | `https://ark.ap-southeast-1.byteplusapi.com` | `ap-southeast-1` | USD |
  | `cn` (Volcengine Ark) | `https://ark.cn-beijing.volces.com/api/v3` | `https://open.volcengineapi.com` | `cn-beijing` | CNY |

  Both use service `ark` and Version `2024-01-01`. Model IDs: cn `doubao-seedance-2-0-260128`, `doubao-seedance-2-5-260628`; each region serves only its own IDs. — [moku-labs/ai PR #15 regions.ts + README](https://github.com/moku-labs/ai/pull/15)
- A user claim (unconfirmed) says the Volcengine virtual portrait library may need a purchased advanced-rights or asset-pack entitlement. — [ArcReel #2249](https://github.com/ArcReel/ArcReel/issues/2249)

### Gaps
- Volcengine tier pricing and quotas in CNY, and whether the CN real-human flow is also invitation-only.
- The cn `doubao-seedance-2-5-260628` ID comes from reseller sources, and moku marks it "id unverified".

---

## 7. ModelArk video generation API: enough for a Node.js script

### Takeaway
Create a task with `POST {base}/contents/generations/tasks` (Bearer API key). The body is `{model, content:[{type:"text",text}, {type:"image_url", image_url:{url}, role}], resolution, ratio, duration, generate_audio, watermark, return_last_frame, …}`. Then poll `GET {base}/contents/generations/tasks/{id}` until `succeeded`, `failed`, `expired` or `cancelled`. Download `content.video_url` at once, because it expires 24 hours after success.

### Cited Findings
**Endpoints**
- `POST /contents/generations/tasks` (create), `GET /contents/generations/tasks/{id}` (retrieve), `GET /contents/generations/tasks` (list; history kept 7 days), `DELETE /contents/generations/tasks/{id}` (cancel or delete).
- Auth: `Authorization: Bearer <API key>`. BytePlus base URL: `https://ark.ap-southeast.bytepluses.com/api/v3`. Video and last-frame URLs are valid for 24 hours.
- Source: [ark-mcp PLAN_ARK_SEED_MULTIMODAL_MCP](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_ARK_SEED_MULTIMODAL_MCP.md); [ark-mcp SPEC](https://github.com/byteplus-sa/ark-mcp/blob/main/specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md)

**Model IDs (BytePlus)**
- `dreamina-seedance-2-0-260128`, `dreamina-seedance-2-0-fast-260128`, `dreamina-seedance-2-0-mini-260615`, `dreamina-seedance-2-5-260628`, and `dreamina-seedance-2-5-premium-260915` (whitelist-only). — [ark-mcp docs/models.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/models.md); [PLAN_ARK_SEED_MULTIMODAL_MCP](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_ARK_SEED_MULTIMODAL_MCP.md)

**Version differences**

| | Seedance 2.0 family | Seedance 2.5 |
|---|---|---|
| Duration | up to 15 s (`duration_range=(-1,15)`; -1 = auto) | up to 30 s |
| Reference images / videos / audios | 9 / 3 / 3 | 30 / 10 / 10 |
| Resolutions | 2.0 standard: 480p, 720p, 1080p, 4k; fast and mini: 480p, 720p | 480p, 720p, 1080p (no 4k); Premium adds 4k |
| Seed / `camera_fixed` | not supported | not supported |
| Draft mode | none | `draft` / `draft_task_id`: draft is 480p, final from a draft is 1080p |

Source: [ark-mcp docs/models.md](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/models.md). **Conflict:** moku lists 2.5 as 480p/720p only and 2.0 as 480p/720p/1080p, with a minimum clip of 4 s — [moku README](https://github.com/moku-labs/ai/pull/15). Verify in the console.

**Content roles**
- Image items: `first_frame`, `last_frame` or `reference_image`.
- Video items: `reference_video`. Audio items: `reference_audio`.
- Images can be HTTPS URLs, `data:<mime>;base64,...`, or `asset://<id>`. Video and audio references must be public HTTPS URLs (or `asset://`).
- Ratios: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`, `21:9`, `adaptive`.
- Other body fields: `resolution`, `ratio`, `duration`, `generate_audio`, `watermark`, `return_last_frame`, `execution_expires_after` (3600–259200 s), `priority` (0–9). There is no negative prompt.
- Source: [ark-mcp src/tools/_seedance_shared.py & schemas.py](https://github.com/byteplus-sa/ark-mcp); [moku README](https://github.com/moku-labs/ai/pull/15)

**Task status and failures**
- Status values: `queued`, `running`, `succeeded`, `failed`, `expired`, `cancelled`.
- On success the video is at `content.video_url`, and the last frame is `content.last_frame_url` when requested.
- Usage reports `completion_tokens`. Cost = tokens / 1e6 × price. A rough token estimate is width × height × 24 × seconds / 1024.
- A `failed` status with a `SensitiveContent` code means moderation blocked the task. A face refusal at submit is HTTP 400 and is not billed.
- Source: [moku README](https://github.com/moku-labs/ai/pull/15)

**Minimal Node.js shape** (assembled from the sources above; untested here)
```js
const BASE = "https://ark.ap-southeast.bytepluses.com/api/v3";
const H = { Authorization: `Bearer ${process.env.ARK_API_KEY}`, "Content-Type": "application/json" };
const body = {
  model: "dreamina-seedance-2-5-260628",
  content: [
    { type: "text", text: "Image 1 is the character. She turns toward camera and smiles." },
    { type: "image_url", image_url: { url: "asset://asset-20260924075358-s9g98" }, role: "reference_image" }
  ],
  resolution: "720p", ratio: "9:16", duration: 5, generate_audio: false, watermark: false
};
const { id } = await (await fetch(`${BASE}/contents/generations/tasks`, { method: "POST", headers: H, body: JSON.stringify(body) })).json();
let t;
do {
  await new Promise(r => setTimeout(r, 10000));
  t = await (await fetch(`${BASE}/contents/generations/tasks/${id}`, { headers: H })).json();
} while (["queued", "running"].includes(t.status));
console.log(t.status, t.content?.video_url, t.error);
```

Asset management, by contrast, is `POST https://ark.ap-southeast-1.byteplusapi.com/?Action=CreateAsset&Version=2024-01-01` with a JSON body `{GroupId, URL, AssetType:"Image", Name, ProjectName}`, signed with HMAC-SHA256 (see Section 2).

### Inferences
- A moodboard app can keep generation on the API key alone. Only the asset-registration step needs AK/SK, and that step could run in a small backend job.

### Gaps
- The official create-task API page (BytePlus doc ID unknown; Volcengine `create-video-generation-task-api`) was not readable, so the exact error-response JSON shape and whether `first_frame` accepts `asset://` are unconfirmed.
- Current official per-token prices are not confirmed. The figures seen ($7.0/M tokens for 2.0, $10.7/M for 2.5) come from third-party summaries.
