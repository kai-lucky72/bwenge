# Bwenge OS - External Tools & Third-Party Services

**Date:** December 1, 2025  
**Phase:** Development  
**Purpose:** Identify all external dependencies needed

---

## 🎯 CRITICAL DEPENDENCIES (Must Have)

### 1. AI & Machine Learning

#### **OpenAI API** 🔴 CRITICAL
**Purpose:** LLM responses, embeddings, audio transcription  
**Services Used:**
- GPT-3.5-turbo / GPT-4 (chat completions)
- text-embedding-ada-002 (vector embeddings)
- Whisper API (audio/video transcription)

**Pricing:**
- GPT-3.5-turbo: $0.0015/1K input tokens, $0.002/1K output tokens
- GPT-4: $0.03/1K input tokens, $0.06/1K output tokens
- Embeddings: $0.0001/1K tokens
- Whisper: $0.006/minute

**Setup:**
```bash
# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

**Monthly Estimate (100 users):**
- Chat: ~$50-200
- Embeddings: ~$10-30
- Transcription: ~$20-50
- **Total: $80-280/month**

**Alternatives:**
- Anthropic Claude (similar pricing)
- Google Gemini (cheaper, but different API)
- Local LLMs (Llama 2, Mistral) - free but needs GPU

---

### 2. Database & Storage

#### **PostgreSQL** 🟢 FREE (Self-hosted)
**Purpose:** Primary database  
**Options:**
- **Development:** Docker container (free)
- **Production Options:**
  - Self-hosted on VPS ($5-20/month)
  - Supabase (free tier: 500MB, then $25/month)
  - AWS RDS ($15-100/month)
  - DigitalOcean Managed ($15-50/month)

**Recommended:** Supabase (includes storage + auth)

---

#### **Redis** 🟢 FREE (Self-hosted)
**Purpose:** Caching, Celery broker, session storage  
**Options:**
- **Development:** Docker container (free)
- **Production Options:**
  - Self-hosted on VPS (free with server)
  - Redis Cloud (free tier: 30MB, then $5/month)
  - AWS ElastiCache ($15-50/month)
  - Upstash (serverless, $0.2/100K commands)

**Recommended:** Redis Cloud or self-hosted

---

#### **Weaviate (Vector Database)** 🟡 FREE/PAID
**Purpose:** Store and search vector embeddings  
**Options:**
- **Development:** Docker container (free)
- **Production Options:**
  - Self-hosted ($10-50/month for VPS)
  - Weaviate Cloud (free tier: 1GB, then $25/month)
  - Alternatives: Qdrant, Pinecone, Chroma

**Recommended:** Weaviate Cloud or self-hosted

**Alternatives:**
- Pinecone ($70/month for 1M vectors)
- Qdrant Cloud (free tier, then $25/month)
- Chroma (self-hosted, free)

---

#### **Object Storage** 🟡 REQUIRED
**Purpose:** Store uploaded files (PDFs, audio, video, 3D models)  
**Options:**

**Option 1: Supabase Storage** (Recommended)
- Free tier: 1GB storage, 2GB bandwidth
- Paid: $0.021/GB storage, $0.09/GB bandwidth
- Includes CDN
- Easy integration
- **Cost:** $0-10/month initially

**Option 2: AWS S3**
- $0.023/GB storage
- $0.09/GB bandwidth
- Requires CloudFront for CDN
- **Cost:** $5-30/month

**Option 3: Cloudflare R2**
- $0.015/GB storage
- FREE egress bandwidth
- Best for high traffic
- **Cost:** $3-15/month

**Option 4: DigitalOcean Spaces**
- $5/month (250GB storage, 1TB bandwidth)
- Simple pricing
- **Cost:** $5-20/month

**Recommended:** Supabase Storage (integrated) or Cloudflare R2 (best value)

---

### 3. Payments (Rwanda Focus)

#### **Mobile Money APIs** 🔴 CRITICAL
**Purpose:** Accept payments in Rwanda

**Option 1: MTN Mobile Money API**
- **Provider:** MTN Rwanda
- **Setup:** Apply at MTN MoMo Developer Portal
- **Fees:** ~2-3% transaction fee
- **Integration:** REST API
- **Documentation:** https://momodeveloper.mtn.com/

**Option 2: Airtel Money API**
- **Provider:** Airtel Rwanda
- **Setup:** Contact Airtel Business
- **Fees:** ~2-3% transaction fee
- **Integration:** REST API

**Option 3: Payment Aggregator (Recommended)**

**Flutterwave** (Best for Rwanda)
- Supports: MTN MoMo, Airtel Money, Bank transfers
- Single API for all methods
- **Fees:** 3.8% per transaction
- **Setup:** https://flutterwave.com/rw
- **Free to integrate**
- **Recommended:** ✅ Use this

**Paystack** (Alternative)
- Supports: Mobile money, cards
- **Fees:** 3.9% per transaction
- **Setup:** https://paystack.com/

**For Development:**
- Use simulation mode (already implemented)
- No cost until production

---

### 4. Email Service

#### **Email Provider** 🟡 REQUIRED
**Purpose:** User verification, password reset, notifications

**Option 1: Resend** (Recommended)
- Free tier: 3,000 emails/month
- $20/month: 50,000 emails
- Modern API, great DX
- **Setup:** https://resend.com/

**Option 2: SendGrid**
- Free tier: 100 emails/day
- $15/month: 40,000 emails
- Established provider
- **Setup:** https://sendgrid.com/

**Option 3: AWS SES**
- $0.10 per 1,000 emails
- Cheapest for high volume
- More complex setup
- **Cost:** $1-10/month

**Option 4: Mailgun**
- Free tier: 5,000 emails/month
- $35/month: 50,000 emails
- Good deliverability

**Recommended:** Resend (best DX) or SendGrid (established)

---

## 🔧 DEVELOPMENT TOOLS (Essential)

### 5. Version Control & CI/CD

#### **GitHub** 🟢 FREE
**Purpose:** Code hosting, CI/CD, collaboration  
**Plan:** Free for public repos, $4/user/month for private  
**Includes:**
- Git hosting
- GitHub Actions (2,000 minutes/month free)
- Issue tracking
- Project management

**Already have:** ✅ Assumed

---

### 6. Container Registry

#### **Docker Hub** 🟢 FREE
**Purpose:** Store Docker images  
**Free tier:** 1 private repo, unlimited public  
**Alternative:** GitHub Container Registry (free)

**Recommended:** GitHub Container Registry (integrated)

---

### 7. Monitoring & Observability

#### **Sentry** 🟡 OPTIONAL (Recommended)
**Purpose:** Error tracking and monitoring  
**Free tier:** 5,000 errors/month  
**Paid:** $26/month for 50,000 errors  
**Setup:** https://sentry.io/

**Alternative:** Self-hosted (free but needs maintenance)

---

#### **Prometheus + Grafana** 🟢 FREE (Self-hosted)
**Purpose:** Metrics and dashboards  
**Already implemented:** ✅ Metrics exposed  
**Setup:** Deploy with Docker Compose

---

#### **Uptime Monitoring**

**Option 1: UptimeRobot** (Free)
- Free tier: 50 monitors, 5-min intervals
- **Setup:** https://uptimerobot.com/

**Option 2: Better Uptime** (Free)
- Free tier: 10 monitors, 3-min intervals
- **Setup:** https://betteruptime.com/

**Recommended:** UptimeRobot (sufficient for start)

---

## 🚀 DEPLOYMENT & INFRASTRUCTURE

### 8. Hosting Platform

#### **Option 1: DigitalOcean** (Recommended for Start)
**Services:**
- Droplets (VPS): $6-12/month
- Managed Kubernetes: $12/month + nodes
- Managed Databases: $15/month
- Spaces (Storage): $5/month

**Estimated Cost:** $30-60/month for small deployment

**Pros:**
- Simple pricing
- Good documentation
- Rwanda-friendly
- Easy to scale

---

#### **Option 2: AWS** (For Scale)
**Services:**
- EC2 (VPS): $5-50/month
- EKS (Kubernetes): $72/month + nodes
- RDS (Database): $15-100/month
- S3 (Storage): $5-30/month

**Estimated Cost:** $100-300/month

**Pros:**
- Most features
- Best for scale
- Global reach

**Cons:**
- Complex pricing
- Steeper learning curve

---

#### **Option 3: Fly.io** (Modern Alternative)
**Services:**
- Apps: $0-50/month
- Postgres: $0-30/month
- Redis: $0-10/month

**Estimated Cost:** $20-90/month

**Pros:**
- Simple deployment
- Good free tier
- Modern platform

---

#### **Option 4: Railway** (Easiest)
**Services:**
- All-in-one platform
- $5/month + usage

**Estimated Cost:** $20-50/month

**Pros:**
- Easiest deployment
- Good for MVP

---

**Recommended Path:**
1. **Development:** Local Docker Compose (free)
2. **Staging:** Fly.io or Railway ($20-30/month)
3. **Production:** DigitalOcean ($50-100/month)
4. **Scale:** AWS/GCP ($200+/month)

---

### 9. Domain & DNS

#### **Domain Name** 🟡 REQUIRED
**Purpose:** bwenge.com or similar  
**Cost:** $10-15/year  
**Providers:**
- Namecheap
- Google Domains
- Cloudflare Registrar

---

#### **Cloudflare** 🟢 FREE (Recommended)
**Purpose:** DNS, CDN, DDoS protection  
**Free tier includes:**
- DNS management
- CDN (unlimited bandwidth)
- SSL certificates
- DDoS protection
- Basic WAF

**Setup:** https://cloudflare.com/

**Recommended:** ✅ Use Cloudflare (essential)

---

## 📱 OPTIONAL BUT RECOMMENDED

### 10. Analytics

#### **PostHog** 🟢 FREE (Self-hosted)
**Purpose:** Product analytics, feature flags  
**Free tier:** 1M events/month  
**Self-hosted:** Free, unlimited  
**Setup:** https://posthog.com/

**Alternative:** Google Analytics (free)

---

### 11. Customer Support

#### **Crisp** 🟢 FREE
**Purpose:** Live chat widget  
**Free tier:** Unlimited conversations  
**Setup:** https://crisp.chat/

**Alternative:** Tawk.to (free)

---

### 12. Documentation

#### **GitBook** 🟢 FREE
**Purpose:** User documentation  
**Free tier:** Public docs  
**Alternative:** Docusaurus (self-hosted, free)

---

## 💰 COST SUMMARY

### Development Phase (Months 1-3)

| Service | Cost | Notes |
|---------|------|-------|
| OpenAI API | $50-100/month | Testing & development |
| Hosting (Fly.io) | $20-30/month | Staging environment |
| Domain | $10/year | One-time |
| Email (Resend) | FREE | Free tier sufficient |
| Monitoring | FREE | Free tiers |
| **TOTAL** | **$70-130/month** | |

---

### Production Phase (Months 4+)

| Service | Cost | Notes |
|---------|------|-------|
| OpenAI API | $200-500/month | 100-500 users |
| Hosting (DigitalOcean) | $50-100/month | VPS + managed services |
| Database (Supabase) | $25/month | Managed Postgres |
| Storage (Cloudflare R2) | $10-20/month | Files + CDN |
| Vector DB (Weaviate Cloud) | $25/month | Managed |
| Email (Resend) | $20/month | 50K emails |
| Payments (Flutterwave) | 3.8% per transaction | Revenue-based |
| Monitoring (Sentry) | $26/month | Error tracking |
| Domain | $1/month | Amortized |
| **TOTAL** | **$357-692/month** | + 3.8% transaction fees |

---

### At Scale (1,000+ users)

| Service | Cost | Notes |
|---------|------|-------|
| OpenAI API | $1,000-2,000/month | High usage |
| Hosting (AWS) | $200-500/month | Kubernetes cluster |
| Database | $100/month | Larger instance |
| Storage | $50-100/month | More files |
| Vector DB | $100/month | More vectors |
| Email | $35/month | Higher tier |
| Payments | 3.8% per transaction | Revenue-based |
| Monitoring | $50/month | More events |
| **TOTAL** | **$1,535-2,885/month** | + transaction fees |

---

## 🎯 RECOMMENDED SETUP FOR START

### Phase 1: MVP (Months 1-3)

**Essential Services:**
1. ✅ OpenAI API ($50-100/month)
2. ✅ Fly.io hosting ($20-30/month)
3. ✅ Cloudflare (FREE)
4. ✅ Resend email (FREE tier)
5. ✅ Domain ($10/year)

**Total: ~$80/month**

**Skip for now:**
- Paid monitoring (use free tiers)
- Managed databases (use Fly.io Postgres)
- Separate storage (use Fly.io volumes)

---

### Phase 2: Launch (Months 4-6)

**Add:**
1. ✅ Flutterwave payments (3.8% fees)
2. ✅ Supabase database ($25/month)
3. ✅ Cloudflare R2 storage ($10/month)
4. ✅ Sentry monitoring ($26/month)

**Total: ~$200/month + transaction fees**

---

### Phase 3: Growth (Months 7+)

**Add:**
1. ✅ Weaviate Cloud ($25/month)
2. ✅ DigitalOcean Kubernetes ($50+/month)
3. ✅ Increased OpenAI budget
4. ✅ Email paid tier ($20/month)

**Total: ~$400+/month**

---

## 📋 SETUP CHECKLIST

### Week 1: Core Services

- [ ] Create OpenAI account and get API key
- [ ] Set up GitHub repository (if not done)
- [ ] Register domain name
- [ ] Set up Cloudflare DNS
- [ ] Create Fly.io account (or chosen hosting)

### Week 2: Development Tools

- [ ] Set up Resend for emails
- [ ] Configure Sentry for error tracking
- [ ] Set up UptimeRobot for monitoring
- [ ] Create development environment

### Week 3: Payment Integration

- [ ] Apply for Flutterwave account
- [ ] Set up test environment
- [ ] Integrate payment webhooks
- [ ] Test payment flows

### Week 4: Production Prep

- [ ] Set up production database
- [ ] Configure object storage
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring and alerts

---

## 🔐 API KEYS TO OBTAIN

**Priority Order:**

1. **OpenAI API Key** 🔴 CRITICAL
   - https://platform.openai.com/api-keys
   - Add payment method
   - Set usage limits

2. **Hosting Account** 🔴 CRITICAL
   - Fly.io / DigitalOcean / AWS
   - Add payment method

3. **Cloudflare Account** 🟡 IMPORTANT
   - https://cloudflare.com/
   - Free tier sufficient

4. **Email Service** 🟡 IMPORTANT
   - Resend / SendGrid
   - Verify domain

5. **Payment Provider** 🟡 IMPORTANT
   - Flutterwave (for Rwanda)
   - Complete KYC process

6. **Monitoring** 🟢 OPTIONAL
   - Sentry
   - UptimeRobot

---

## 💡 COST OPTIMIZATION TIPS

### 1. Start Small
- Use free tiers initially
- Self-host what you can
- Scale as you grow

### 2. OpenAI Optimization
- Use GPT-3.5-turbo (cheaper than GPT-4)
- Implement response caching
- Set token limits
- Use streaming to reduce perceived latency

### 3. Storage Optimization
- Compress files before storage
- Use CDN for static assets
- Implement file size limits
- Clean up old files

### 4. Database Optimization
- Use connection pooling
- Implement query caching
- Archive old data
- Use read replicas only when needed

### 5. Monitoring
- Start with free tiers
- Upgrade only when limits hit
- Use sampling for high-volume metrics

---

## 🚨 CRITICAL DEPENDENCIES SUMMARY

**Must have before starting:**
1. ✅ OpenAI API key
2. ✅ Hosting account (Fly.io/DigitalOcean)
3. ✅ Domain name
4. ✅ Cloudflare account

**Can add later:**
- Email service (use console logs initially)
- Payment integration (use simulation)
- Monitoring (use basic logging)
- Managed databases (use Docker initially)

---

## 📞 NEXT STEPS

1. **This Week:**
   - Get OpenAI API key
   - Choose hosting provider
   - Register domain
   - Set up Cloudflare

2. **Next Week:**
   - Set up development environment
   - Configure email service
   - Set up monitoring

3. **Month 1:**
   - Deploy to staging
   - Test all integrations
   - Prepare for production

---

**Total Initial Investment:** $80-130/month  
**Time to Setup:** 2-4 weeks  
**Recommended Budget:** $200/month for first 3 months

