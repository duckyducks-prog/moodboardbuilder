# Register faces first, then Seedance animates them

**Other tools don't send your image to Seedance as it is. They register it with ByteDance first.** Seedance 2.5 blocks your photoreal AI faces on OpenRouter because ByteDance (the company behind Seedance) runs a face check on every uploaded image. The check can't tell a realistic AI face from a real person's photo, so it refuses both with `InputImageSensitiveContentDetected.PrivacyInformation`. The only exception is a face that comes in through one of ByteDance's approved channels, mainly its **virtual portrait library**. The image is uploaded there as a declared fictional character, gets an ID like `asset://asset-2026…`, and Seedance accepts that ID. Tools that seem to "accept any image" are doing that upload for you in the background ([Cloudflare](https://developers.cloudflare.com/ai/models/bytedance/seedance-2.5/); [Comfy docs](https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-0-real-human)). OpenRouter has no documented way to do this, so it can't fix your problem today. You can keep Seedance 2.5 and your Node.js scripts. The simplest switch is **Cloudflare Workers AI with the `use_virtual_avatar: true` setting**. The most direct and controllable option is **BytePlus ModelArk** (ByteDance's own API platform) on its **free "Advanced Entry" tier**. One caveat about the sources: the research network couldn't open ByteDance's official pages. Official wording comes through search snippets and a BytePlus-linked code repository, and the vendor claims below are marked as such.

## The block reacts to how the face looks, not where it came from

ByteDance's rule is simple: Seedance 2.0 and 2.5 "do not support directly uploading reference images/videos that contain real human faces" ([SeedRouter, quoting ModelArk](https://seedrouter.ai/blog/seedance-real-person-error)). The goal is to stop deepfakes and protect people's likeness. The check runs inside ByteDance's own system, so **no reseller can switch it off**, OpenRouter included. The catch for you is that the check judges how realistic a face looks, not whether the person exists. The error means the system "considered the image a possible real-person image", which "does not prove the image actually shows a real person" ([YingTu](https://yingtu.ai/en/blog/seedance-2-0-human-face)).

Developers keep reporting the same problem. A photoreal render of an invented character was refused with the same `PrivacyInformation` code ([openstory #1927](https://github.com/openstory-so/openstory/issues/1927)). Chinese users hit it with AI-generated realistic people used as a first frame ([ArcReel #2249](https://github.com/ArcReel/ArcReel/issues/2249)). ComfyUI updated its site copy to warn that Seedance blocks realistic faces "even when they are AI-generated". One of its developers saw one photoreal AI portrait refused and another accepted, which suggests the check runs **image by image and is not fully predictable** ([ComfyUI_frontend PR #19638](https://github.com/Comfy-Org/ComfyUI_frontend/pull/19638)). Adobe users report the same false flags ([Adobe Community](https://community.adobe.com/questions-404/seedance-dont-work-correctly-detects-human-face-and-is-not-human-face-is-created-with-ia-1630600)).

One upside: a refusal costs nothing. The error comes back before a job is created, so **blocked requests aren't billed** ([moku-labs PR #15](https://github.com/moku-labs/ai/pull/15); [APIYI](https://docs.apiyi.com/en/api-capabilities/seedance2/asset-library)).

## Three approved channels, and every face-friendly tool uses one

ByteDance documents three ways a face can get past the check. All three prove where the face came from ([Clipdance](https://clipdance.ai/blog/seedance-2-real-face-workaround); [BytePlus docs 2333565](https://docs.byteplus.com/en/docs/ModelArk/2333565)):

| Channel | What it's for | Fits your AI characters? |
|---|---|---|
| **Virtual portrait library** | Upload a fictional face once, get an `asset://` ID, use that ID in Seedance | **Yes, this is the main route** |
| **Real-person library** | A real person passes a phone liveness check and consents (invited users only) | No. An AI character has no living person to verify |
| **Trusted outputs** | Untouched images or videos made by ByteDance's own models (for example Seedream 5.0 lite) in the same account, reused within 30 days | Only if you generate the character inside ByteDance's system *(secondhand: official text quoted by [reapi](https://reapi.ai/blog/seedance-not-eligible-explained))* |

Here is how the virtual portrait route works, per a BytePlus-linked repository whose authors tested it live on Seedance 2.5 in September 2026 ([byteplus-sa/ark-mcp](https://github.com/byteplus-sa/ark-mcp/blob/main/docs/assets.md); [spec](https://github.com/byteplus-sa/ark-mcp/blob/main/specs/SPEC_MODELARK_ASSET_LIBRARY_CONTRACT.md)). You create a "group" for each character. You upload the image from a public web link. You wait until its status reads **Active**. Then your Seedance request uses `asset://<id>` in place of the image link. One rule matters: the library is for faces that **"must not resemble any real person"**. It's for fictional characters, not a way to sneak in real people.

ComfyUI shows what this looks like when it's packaged for users. Its node turns AI portraits into assets with "no extra check". Real people go through a one-time liveness check of under 30 seconds ([Comfy blog](https://blog.comfy.org/p/unlock-seedance20-real-human-video-generation)). So other tools do accept your images, but none of them accepts *any* image. They register fictional faces quietly and make real people verify themselves.

## Which platforms you can script from Node.js

| Platform | How faces get through | Effort from Node.js | Cost notes | Confidence |
|---|---|---|---|---|
| **Cloudflare Workers AI** | `use_virtual_avatar: true` sends your images through ByteDance's virtual-avatar library before generation. Covers Seedance 2.0, 2.0 Fast, 2.0 Mini and **2.5** | **Lowest: one extra setting** | Not covered in this research; check Cloudflare's pricing | **Verified** (Cloudflare's own docs) ([Cloudflare 2.5](https://developers.cloudflare.com/ai/models/bytedance/seedance-2.5/)) |
| **BytePlus ModelArk (direct)** | You upload to the virtual portrait library yourself, then use `asset://` | Medium: uploads need a second, signed key (Access Key / Secret Key, or AK/SK); generation uses your normal API key | Library tiers below; video tokens billed as usual | **Verified** via official doc snippets plus the BytePlus-linked repo |
| **APIYI** | You create the asset group and upload yourself (no auto-upload), then use `asset://` | Medium | *Claim:* virtual-face access is free on APIYI's channel ([APIYI](https://docs.apiyi.com/en/api-capabilities/seedance2/overview)) | Own docs ([APIYI](https://docs.apiyi.com/en/api-capabilities/seedance2/asset-library)) |
| **PiAPI** | Upload to PiAPI's Asset Library, pass review | Medium | $0.053/s at 480p, $0.106/s at 720p (page about 6 months old; Seedance 2.0) ([PiAPI](https://piapi.ai/seedance-2-0)) | Own pages; details unread |
| **OrcaRouter** | `asset://` references; only Active assets work | Medium | Not found | Own docs ([OrcaRouter](https://docs.orcarouter.ai/seedance-video/asset-library)) |
| **EvoLink** | Says it supports real faces "after verification" | Unclear | *Claim, April 2026, Seedance 2.0:* $0.092–0.199/s, no face surcharge ([EvoLink](https://evolink.ai/blog/seedance-2-0-real-human-video-api-guide)) | **Vendor claim only** |

**Cloudflare is the closest thing to "just accept my image".** Its own docs say the flag is "intended for AI-generated/virtual character avatars that would otherwise be blocked by face or deepfake detection" ([Cloudflare](https://developers.cloudflare.com/ai/models/bytedance/seedance-2.0-fast/)). That is your exact situation.

Going **direct to BytePlus** takes more setup but gives you the most control. Library access comes with "Advanced Creation Rights", which has four tiers ([ark-mcp plan](https://github.com/byteplus-sa/ark-mcp/blob/main/plans/PLAN_MODELARK_ASSET_LIBRARY.md), citing BytePlus's purchase guide):

| Tier | Price | API access | Assets / groups | Upload speed |
|---|---|---|---|---|
| Basic | Free | Console only | 50 / 50 | 3 per minute |
| **Advanced Entry** | **Free** | **Yes** | **50 / 50** | **3 per minute** |
| Advanced | $1,400/month | Yes | 1M / 1M | 120 per minute |
| Advanced Premium | $4,200/month | Yes | 5M / 5M | 300 per minute |

The free Entry tier is enough for a moodboard workflow with up to 50 character images. Uploading assets costs nothing extra; you pay for video generation as normal ([moku-labs PR #15](https://github.com/moku-labs/ai/pull/15)). Two warnings. First, if you ever let a paid tier lapse, assets created during it are **deleted permanently** after a 15-day grace period. Second, the per-token video prices circulating online ($10.7 per million tokens for 2.5) are **secondhand and unconfirmed**. Check them in the console.

A few platforms are known not to help. fal.ai shows no face or asset option at all ([fal 2.5](https://fal.ai/models/bytedance/seedance-2.5/reference-to-video)). Third-party guides say Replicate and WaveSpeed hit the same block (unconfirmed) ([Segmind](https://blog.segmind.com/seedance-2-0-error-guide-every-error-explained-with-fixes/)).

A Japanese post from April 2026 says Higgsfield and Freepik accept realistic people, but it's **unverified and contradicted** by other guides ([note.com](https://note.com/creative_edge/n/n91b776e20b9d?hl=en)). Neither platform has a public API for this anyway.

## OpenRouter sends plain links and has no face route

OpenRouter's video API accepts only HTTPS image links in `input_references` and `frame_images` ([OpenRouter cookbook](https://openrouter.ai/docs/cookbook/video-generation/reference-to-video)). It rejects `data:` uploads with a 400 error ([issue #101](https://github.com/Reid-Surmeier/Image-generation-pipline/issues/101)).

This research found **no documented `asset://` support, no virtual-avatar setting and no provider option for faces**. OpenRouter's own Seedance 2.5 review says references can carry "a face" without mentioning the block ([OpenRouter blog](https://openrouter.ai/blog/insights/seedance-2-5-review/)).

The practical result: OpenRouter forwards your image link to ByteDance, and ByteDance's check refuses it. **This is not something you can fix in your scripts.** OpenRouter's Discord and changelog couldn't be checked, so a recent change is possible but unconfirmed. OpenRouter still works for shots with no realistic faces, such as landscapes, products and stylised characters.

## Skip the "bypass" tricks

Some sites promote character-sheet grids, overlays, added noise, cropping, blur or sunglasses to slip faces past the filter ([ViralTwin](https://www.viraltwin.app/blog/pass-seedance-face-filter); [VicSee](https://vicsee.com/blog/seedance-content-filter)). **Avoid them.** They deliberately defeat a consent safeguard and probably break the terms of service. They also work unreliably, because the check is per image, and they can fail at the output filter *after* you've paid for the generation ([Clipdance](https://clipdance.ai/blog/seedance-2-real-face-workaround); [YingTu](https://yingtu.ai/en/blog/seedance-2-0-human-face)). The approved routes are cheaper, more reliable and allowed.

## Conclusion

The idea that other tools accept any image is half right. They accept your AI characters because they register them as declared fictional faces behind the scenes. Real people's photos still need that person's live consent everywhere. So the fix is to **add a registration step**, not to find a looser host.

**Recommended path:** keep Seedance 2.5 and move face shots off OpenRouter. **Start with Cloudflare Workers AI and set `use_virtual_avatar: true`.** It's one setting in a normal API call from Node.js, and it's documented for exactly this case. Test it on a few of your blocked images first, because the docs don't say whether some faces still fail registration.

If you want ByteDance's own platform, or Cloudflare's pricing or limits don't suit you, **open a BytePlus ModelArk account on the free Advanced Entry tier**. Then:

1. Sign the authorization letter once in the console.
2. Create an AK/SK key with `ArkFullAccess`.
3. Have your script upload each character image, wait for "Active" and then call Seedance 2.5 with `asset://`.

Either way, keep OpenRouter for face-free shots if you like it. And for new characters, consider creating them with Seedream inside the same BytePlus account so they qualify as trusted outputs. Treat that route as secondhand until you test it.
