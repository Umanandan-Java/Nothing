import sqlite3
import os

DATABASE_FILE = "econsultation.db"

# --- Schema Definition based on your final PDF ---
# Using multiline strings to hold the CREATE TABLE statements
CREATE_DRAFTS_TABLE = """
CREATE TABLE IF NOT EXISTS drafts (
    draft_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    draft_ai_summary TEXT,
    word_cloud_image_path TEXT
);
"""

CREATE_SECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sections (
    section_id INTEGER PRIMARY KEY,
    draft_id INTEGER NOT NULL,
    section_title TEXT NOT NULL UNIQUE,
    section_content TEXT,
    section_ai_summary TEXT,
    section_ai_key_points TEXT,
    word_cloud_image_path TEXT,
    FOREIGN KEY (draft_id) REFERENCES drafts(draft_id)   
);
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    address TEXT,
    country TEXT,
    state TEXT,
    is_organization BOOLEAN DEFAULT 0,
    organization_name TEXT,
    industry TEXT CHECK(industry IN ('Education', 'Healthcare', 'Finance', 'Technology', 'Government', 'Non-Profit', 'Other')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SUBMISSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS submissions (
    submission_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    draft_id INTEGER NOT NULL,
    otp_verified BOOLEAN DEFAULT 0,
    submission_status TEXT NOT NULL DEFAULT 'completed',
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (draft_id) REFERENCES drafts(draft_id)
);
"""

CREATE_COMMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS comments (
    comment_id INTEGER PRIMARY KEY,
    submission_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    action_type TEXT NOT NULL CHECK(action_type IN ('In Agreement', 'Suggest removal', 'Suggest modification', 'Implicit Agreement')),
    comment_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    sentiment_label TEXT,
    sentiment_score REAL,
    ai_summary TEXT,
    word_cloud_image_path TEXT,
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id)   
);
"""

# --- Data Insertion Queries ---
# All the INSERT statements you need to populate the database with fake data.
INSERT_DATA = """
-- The SQL INSERT statements for drafts, sections, users, submissions, and comments go here.
-- This is a very long string, so it's kept separate for clarity.
INSERT INTO drafts (draft_id, title, description) VALUES
(1, 'The Digital India Act, 2025', 'A comprehensive framework for data protection, intermediary liability, and regulation of emerging technologies.'),
(2, 'The Corporate Governance and ESG Disclosure Bill, 2025', 'A bill to enforce stricter corporate governance norms and mandatory Environmental, Social, and Governance (ESG) reporting.'),
(3, 'The National Green Energy Framework, 2025', 'Policy outlining subsidies, carbon taxes, and infrastructure development for renewable energy.');

INSERT INTO sections (section_id, draft_id, section_title, section_content) VALUES
(1, 1, 'Section 5: Data Localisation Mandates', 'All sensitive personal data of Indian citizens must be stored exclusively on servers located within India.'),
(2, 1, 'Section 12: Intermediary Liability and Safe Harbour', 'Redefines the conditions under which social media platforms are granted safe harbour protections.'),
(3, 1, 'Section 22: Regulation of AI Models', 'Establishes a regulatory body to classify and audit high-risk AI systems deployed in critical sectors.'),
(4, 2, 'Section 8: Mandatory ESG Reporting', 'All listed companies with a turnover above Rs. 500 Cr must publish an annual ESG report based on a standardized format.'),
(5, 2, 'Section 15: Independent Director Quotas', 'Mandates that at least 50% of the board members of listed companies must be Independent Directors.'),
(6, 2, 'Section 21: Executive Compensation Caps', 'Introduces a cap on the cash component of executive compensation, linking it to the median employee salary.'),
(7, 3, 'Section 4: Solar Power Subsidies', 'Details the subsidy structure for rooftop solar panel installations for residential and commercial properties.'),
(8, 3, 'Section 9: Carbon Tax Implementation', 'A phased implementation of a carbon tax on industries based on their greenhouse gas emissions.'),
(9, 3, 'Section 14: Electric Vehicle Charging Infrastructure', 'Mandates all new commercial buildings to allocate 10% of parking space for EV charging stations.');

INSERT INTO users (user_id, first_name, last_name, email, phone, address, country, state, is_organization, organization_name, industry) VALUES
(1, 'Priya', 'Sharma', 'priya.sharma@email.com', '9876543210', 'Indiranagar, Bangalore', 'India', 'Karnataka', 0, NULL, NULL),
(2, 'Vikram', 'Singh', 'vikram.singh@law.edu', '9876543211', 'Model Town, Delhi', 'India', 'Delhi', 0, NULL, NULL),
(3, 'Anjali', 'Desai', 'anjali.desai.ret@email.com', '9876543212', 'Malabar Hill, Mumbai', 'India', 'Maharashtra', 0, NULL, NULL),
(4, 'Raj', 'Patel', 'raj.patel.biz@email.com', '9876543213', 'Navrangpura, Ahmedabad', 'India', 'Gujarat', 0, NULL, NULL),
(5, 'Kabir', 'Verma', 'kabir.sarcasm@email.com', '9876543214', 'Koregaon Park, Pune', 'India', 'Maharashtra', 0, NULL, NULL),
(6, 'Rohan', 'Gupta', 'rohan.g@innovatenow.com', '9876543215', 'Hitech City, Hyderabad', 'India', 'Telangana', 1, 'InnovateNow Tech Pvt. Ltd.', 'Technology'),
(7, 'Sunita', 'Krishnan', 'sunita.k@veritaslegal.com', '9876543216', 'Nariman Point, Mumbai', 'India', 'Maharashtra', 1, 'Veritas Legal LLP', 'Finance'),
(8, 'Arjun', 'Menon', 'arjun.m@greenfuture.org', '9876543217', 'Besant Nagar, Chennai', 'India', 'Tamil Nadu', 1, 'Green Future Foundation', 'Non-Profit'),
(9, 'Amitabh', 'Chaudhary', 'ac@bigcorp.com', '9876543218', 'Gurgaon, Haryana', 'India', 'Haryana', 1, 'MegaCorp Industries', 'Finance'),
(10, 'Siddharth', 'Jain', 'sid@fintechstart.com', '9876543219', 'HSR Layout, Bangalore', 'India', 'Karnataka', 1, 'Fintech Innovations Ltd', 'Technology');

INSERT INTO submissions (submission_id, user_id, draft_id) VALUES
(101, 1, 1), (102, 2, 1), (103, 3, 2), (104, 4, 2), (105, 5, 1), (106, 6, 1), (107, 7, 1), (108, 8, 3), (109, 9, 2), (110, 7, 2), (111, 4, 3), (112, 1, 2), (113, 8, 1), (114, 10, 1), (115, 5, 2);

INSERT INTO comments (submission_id, section_id, action_type, comment_text) VALUES
(101, 1, 'Suggest modification', 'While the principle of data sovereignty is important, mandating exclusive storage within India is technically challenging and financially burdensome for startups. This will create data silos and hinder access to global cloud services that offer superior security and scalability. A more pragmatic approach would be to mandate a copy of the data to be stored in India, while allowing processing on global infrastructure. This achieves security without crippling innovation.'),
(101, 3, 'Suggest modification', 'Section 22 is a necessary step, but the term "high-risk AI" is dangerously ambiguous. The draft must provide a concrete, annexed list of what constitutes critical sectors and high-risk applications. Without this clarity, the regulatory body could wield arbitrary power, creating an environment of uncertainty that would deter research and development in the AI space. The audit process must also be transparent and well-defined.'),
(102, 2, 'Suggest removal', 'This section''s attempt to dilute the safe harbour provisions contravenes established global legal principles and risks creating a chilling effect on free speech. Making platforms liable for third-party content without proof of actual knowledge or malicious intent, as established in the Shreya Singhal judgment, is legally unsustainable. This will force platforms to engage in pre-emptive censorship just to avoid litigation, which is a detriment to public discourse.'),
(105, 1, 'In Agreement', 'Oh, absolutely, data localisation is a fantastic idea! My vacation photos are surely a matter of national security and must be protected from foreign eyes at all costs. I feel so much safer knowing my data will be stored on a local server, which will undoubtedly be just as secure and efficient as the multi-billion dollar infrastructures run by global tech giants. It’s not like India has ever had issues with infrastructure management. A truly visionary move for a self-reliant digital future.'),
(105, 3, 'In Agreement', 'A government body to regulate AI? Wonderful! I''m sure a committee of lifelong bureaucrats will have the nuanced technical expertise to fairly audit complex neural networks. They will certainly make unbiased, lightning-fast decisions that foster innovation. I eagerly await the simplified, 300-page form we''ll need to fill out in triplicate to get our new AI-powered toaster approved. This will definitely help us compete with Silicon Valley.'),
(107, 1, 'Suggest modification', 'We submit that the mandate for exclusive data storage under Section 5 imposes a disproportionate restriction on the freedom of trade and commerce. This provision may be ultra vires Article 19(1)(g) of the Constitution. A less intrusive measure, such as data mirroring, would suffice to meet the state''s objective of ensuring access for law enforcement agencies without imposing onerous costs and technical hurdles on data fiduciaries. We recommend a revision to this effect.'),
(107, 2, 'Suggest removal', 'We draw attention to Section 12. The proposed framework for intermediary liability appears to conflate the roles of publisher and platform. Imposing liability for content without a judicial order or clear evidence of incitement is a departure from settled law. Such a provision is vulnerable to being struck down for violating Articles 14 and 19 of the Constitution, as it encourages arbitrary censorship and lacks procedural safeguards for content creators and platforms alike.'),
(106, 1, 'Suggest removal', 'Section 5 is a startup killer. The capital expenditure required to comply with data localisation is prohibitive for early-stage companies. This creates a protectionist moat for large, established players and foreign corporations with deep pockets who can afford local data centers. This directly harms the government''s "Startup India" initiative. We strongly recommend this clause be entirely removed to ensure a level playing field for domestic innovators.'),
(106, 3, 'Suggest modification', 'While we support responsible AI, the regulatory framework in Section 22 should be a "light-touch" system focused on post-facto audits rather than pre-approval. A pre-approval system will drastically increase the time-to-market for innovative AI products. The regulator should work with the industry to create standards and best practices, not act as a gatekeeper. Let the market decide which products succeed, with the government stepping in only when harm is demonstrated.'),
(103, 4, 'In Agreement', 'As a former auditor, I wholeheartedly support Section 8. For too long, companies have paid lip service to social and environmental responsibilities. A standardized ESG reporting format will finally allow investors and the public to compare apples to apples. This brings much-needed transparency and will force management to think beyond quarterly profits. The cost of compliance is a small price to pay for building long-term, sustainable and ethical businesses.'),
(103, 6, 'Suggest removal', 'Section 21, which caps executive compensation, is well-intentioned but misguided. This will lead to a brain drain of top talent to other countries. Companies must be free to offer competitive salaries to attract the best leaders. The issue is not the amount but the lack of transparency. The focus should be on strengthening the "say on pay" rules, giving shareholders more power to approve or reject compensation packages, rather than imposing an arbitrary government cap.'),
(104, 4, 'Suggest modification', 'I own a small listed company, and the ESG reporting requirement in Section 8 is a massive burden. I don''t have a dedicated department for this. This is another compliance nightmare that increases my costs and takes my focus away from actually running my business. Why should a company with a turnover of Rs. 501 Cr have the same reporting burden as one with Rs. 50,000 Cr? The threshold should be much higher, or the reporting format for smaller companies should be drastically simplified.'),
(109, 5, 'Suggest removal', 'The proposal in Section 15 to have 50% independent directors is operationally unworkable and counterproductive. While independence is important, a board heavily skewed towards non-executive directors who lack deep, intrinsic knowledge of the company''s operations can lead to poor strategic decision-making. The current 1/3rd rule is adequate. A better approach is to strengthen the definition of "independence" and enhance the role and power of the audit and nomination committees.'),
(109, 6, 'Suggest modification', 'A government-mandated cap on executive compensation is an overreach and interferes with the free market principles that guide private enterprise. Linking pay to the median salary is a flawed metric that doesn''t account for skill, risk, and global market rates for leadership. It will simply incentivize companies to outsource low-wage jobs to manipulate the median. Instead, the link should be to long-term performance metrics like market cap growth and shareholder return, as approved by the shareholders.'),
(115, 6, 'In Agreement', 'A cap on CEO salaries? Bravo! I’m sure this will magically solve income inequality overnight. Top executives, faced with the horror of earning only 100 times the median salary instead of 500, will surely find newfound humility and work purely for the love of the game. It’s a good thing talent is not a global commodity and that our best leaders would never dream of moving to a company in Singapore or Dubai for a better pay package. This policy has no potential downsides whatsoever.'),
(108, 7, 'Suggest modification', 'The solar subsidy structure in Section 4 is a positive start, but it disproportionately benefits wealthy individuals and large commercial entities who can afford the initial capital outlay. There is no clear provision for low-income households or housing societies. The policy should include a zero-upfront-cost EMI model or community solar projects to ensure that the green transition is equitable and does not leave the poor behind.'),
(108, 8, 'In Agreement', 'The Carbon Tax outlined in Section 9 is a landmark, courageous step towards making polluters pay. This is the single most effective policy tool to drive industries towards cleaner technologies. We commend the government for its vision. We do suggest, however, that the revenue generated from this tax must be statutorily ring-fenced and used exclusively for funding renewable energy projects and supporting communities affected by the transition.'),
(102, 1, 'In Agreement', 'I find the principle of data localisation in Section 5 to be in perfect alignment with national interests. In an era of cyber-warfare and digital colonization, ensuring that our citizens'' data is governed by our laws, on our soil, is a non-negotiable aspect of sovereignty. The arguments about cost made by corporations are often exaggerated and overlook the long-term strategic benefits of building a robust domestic data infrastructure.'),
(104, 5, 'In Agreement', 'Having more independent directors is always a good thing for small investors like me. It reduces the chance of the founding family running the company like a personal fiefdom. Section 15 brings more accountability and ensures there is a truly objective voice in the boardroom that can question management''s decisions without fear. This is a very welcome change.'),
(111, 7, 'Suggest removal', 'As a small factory owner, I don''t understand these solar subsidies. The upfront cost is still too high, even with the discount, and the process to get the subsidy is full of red tape. The government should focus on providing reliable, cheap grid electricity instead of pushing us towards these complex solutions. This policy only seems to benefit the solar panel manufacturing companies.'),
(111, 8, 'Suggest modification', 'A carbon tax will destroy small industries. We operate on thin margins and cannot afford another tax. This will make my products more expensive than cheap imports. The government must provide significant grants and technological support for us to transition to greener methods before imposing a punitive tax. This is like asking a man to swim after tying his hands. We need help, not just penalties.'),
(112, 4, 'Suggest modification', 'The concept of ESG reporting is sound, but the format and details should not be a one-size-fits-all solution dictated by the government. The industry bodies like CII and FICCI should be allowed to develop sector-specific frameworks that are more relevant and less burdensome. Let the experts, not the bureaucrats, define what makes sense for each industry. This approach would be far more effective.'),
(110, 5, 'Suggest modification', 'Our firm opines that while the increase in the quota for independent directors under Section 15 is laudable, the definition of "independence" itself remains weak. The draft fails to address the issue of long tenures and familial relationships with non-executive promoters. We recommend a stricter definition of independence, a mandatory cooling-off period, and a cap on the total tenure of any independent director to ensure their judgment remains uncompromised.'),
(113, 1, 'Suggest removal', 'Data localisation under Section 5 is an environmental concern. Building and maintaining massive data centers in India will require immense amounts of energy and water, putting a strain on our already scarce resources. It is more sustainable to leverage the hyper-efficient, green data centers that global cloud providers have already built in regions with cooler climates and abundant renewable energy. This policy is environmentally short-sighted.'),
(114, 2, 'Suggest modification', 'The new definition of intermediary liability in Section 12 is problematic for AI-driven platforms. Our platform uses algorithms to moderate content. Under the new draft, if the algorithm makes an error, would the company lose its safe harbour status? This ambiguity needs to be clarified. There must be a provision that distinguishes between programmatic moderation and willful negligence, otherwise it will stifle the use of AI for content safety.'),
(101, 2, 'In Agreement', 'I agree with redefining intermediary liability. For too long, large social media platforms have hidden behind "safe harbour" while profiting from the spread of misinformation and hate speech. This change rightfully places the onus on them to invest more in moderation and be accountable for the content they amplify. Freedom of speech is not the freedom to cause harm without consequence. This is a necessary move to make the internet a safer space.'),
(106, 2, 'Suggest removal', 'Section 12 is a recipe for disaster. This will force every tech platform to become a censor. Our small startup cannot afford a massive legal team to review every user comment. We will be forced to either over-censor and alienate our users, or face crippling lawsuits. This section disproportionately harms new Indian startups and creates an insurmountable barrier to entry, while large foreign companies can absorb the litigation costs.'),
(108, 9, 'Suggest removal', 'A phased implementation of carbon tax is not enough; it must be accompanied by a "Just Transition" fund. Section 9 will lead to job losses in traditional sectors like coal and thermal power. Where is the plan to retrain and reskill these workers? The revenue from the tax cannot just go to new green projects; a significant portion must be allocated to provide social security and new employment opportunities for those displaced by this policy.'),
(109, 4, 'Suggest modification', 'Our conglomerate has been voluntarily publishing a comprehensive sustainability report for over a decade. The government’s standardized ESG format in Section 8 is too rigid and focuses excessively on compliance rather than impact. It may lead to a "tick-box" mentality. We propose that the government sets broad principles but allows companies the flexibility to report in a manner that is most relevant to their specific industry and stakeholders, using global standards like GRI or SASB.'),
(115, 4, 'Suggest modification', 'Oh, splendid, an ESG report! Another opportunity for corporate jargon artists to produce a glossy, 100-page document full of pictures of smiling children and thriving trees, all while the company’s factory quietly pollutes the river next door. This standardized format will surely put an end to greenwashing. I am certain that the numbers reported will be 100% accurate and never, ever manipulated to look good. This is a foolproof plan for corporate accountability.'),
(103, 5, 'In Agreement', 'I completely support raising the quota of independent directors to 50%. This is about balancing power. The executive directors, by nature, are focused on operations, and their perspective can be narrow. Independent directors bring diverse experience, an outside view, and a focus on long-term strategy, governance, and ethics. A 50-50 balance ensures that neither side can dominate the board and that decisions are made more democratically and with greater scrutiny.'),
(104, 6, 'Suggest modification', 'Capping executive salary is not the right way. It is simple jealousy politics. Instead, why not make the link to performance more transparent and strong? The rule should be that if the company''s share price goes down, the CEO''s salary also goes down significantly. And if shareholders vote against the salary package, it has to be changed. Let the owners of the company—the shareholders—decide the salary, not the government.'),
(110, 4, 'Suggest modification', 'With reference to Section 8, the proposed timeline for implementation of mandatory ESG reporting is overly aggressive. For companies to collect, audit, and report this data accurately, they need to establish new internal systems. A one-year transition period is insufficient. We recommend a phased rollout over three years, starting with the top 100 companies by market capitalization and then expanding the scope gradually. This will ensure higher quality of disclosures.'),
(112, 5, 'Suggest modification', 'While the intent of increasing independent directors is good, the pool of qualified, truly independent individuals in India is limited. Mandating a 50% quota under Section 15 will lead to the same set of individuals sitting on multiple boards, which defeats the purpose. This will lead to "over-boarding" and reduce their effectiveness. The focus should be on building capacity and training a new generation of independent directors before enforcing such a drastic quota.'),
(114, 1, 'Suggest modification', 'The definition of "sensitive personal data" in the context of data localisation needs to be extremely precise. As a fintech company, we handle financial data which is sensitive. But is user browsing behavior for financial products also sensitive? The ambiguity in Section 5 could lead to over-compliance, where we are forced to store vast amounts of non-critical data locally, leading to massive, unnecessary costs. The draft must clearly define these categories.'),
(107, 3, 'In Agreement', 'Our firm concurs with the necessity of establishing a regulatory body for AI under Section 22. The potential for AI to cause widespread harm in areas like autonomous vehicles, medical diagnostics, and algorithmic trading is significant. Leaving such technologies completely unregulated would be a dereliction of the state''s duty to protect its citizens. We believe a well-defined regulatory framework will provide legal certainty and foster public trust, which is essential for the adoption of AI technologies.'),
(102, 3, 'Suggest removal', 'A pre-emptive regulatory body for AI, as suggested in Section 22, is a classic case of putting the cart before the horse. Innovation in AI happens at a blistering pace, and any government committee will be perpetually behind the curve, stifling progress with outdated rules. The UK’s model of pro-innovation, sector-specific regulation is a far better approach. We should regulate the *use-case* of AI (e.g., its use in credit scoring), not the *technology* itself. This section should be removed and rethought entirely.'),
(113, 8, 'Suggest modification', 'A carbon tax is necessary, but Section 9 unfairly clubs all industries together. A steel plant and a software company have vastly different carbon footprints and abilities to transition. The tax structure needs to be highly granulated by sector, with different rates and timelines. Applying a uniform tax will disproportionately harm our manufacturing sector, which is the backbone of our economy, while having little impact on the service industry.'),
(111, 9, 'Suggest modification', 'The mandate for EV charging stations in new buildings is a good idea, but 10% is too low to be meaningful. This feels like a token gesture. If we are serious about an EV transition, this number should be at least 25-30%. Furthermore, the government must also create provisions for retrofitting older buildings with charging infrastructure, which is a far bigger challenge. Section 14 is a timid step when a bold leap is required.'),
(101, 8, 'In Agreement', 'The introduction of a carbon tax in Section 9 is an economically and environmentally sound policy. By internalizing the external cost of pollution, it creates a powerful market-based incentive for companies to innovate and reduce their emissions. This is far more efficient than a command-and-control regulatory approach. The phased implementation will give industries adequate time to adapt.'),
(103, 9, 'Suggest removal', 'A carbon tax is a regressive tax that will be passed on to the consumers. The price of everything from cement to electricity will go up, and it will hurt the common citizen the most. Companies will just increase prices. This is not the right time to introduce such a policy when we are already dealing with inflation. The government should provide incentives for going green, not penalties.'),
(104, 8, 'In Agreement', 'This carbon tax is a very good step. As a responsible businessman, I believe all industries must be accountable for their impact on the environment. For too long, pollution has been a cost borne by society, not by the polluter. Section 9 finally corrects this. It will be challenging initially, but it will force us all to become more efficient and innovative in the long run, which is good for the country and for our future generations.'),
(115, 8, 'Suggest modification', 'So now we add a carbon tax that makes everything more expensive for the middle class, while large corporations with smart accountants will find loopholes to avoid it. I''m sure the tax revenue will be used with 100% efficiency and will definitely not get lost in bureaucracy. It is comforting to know that my higher electricity bill is directly helping plant a tree somewhere, probably. A truly equitable way to solve a global crisis.'),
(102, 9, 'Suggest modification', 'The legality of a central government-imposed carbon tax as per Section 9 might face challenges from states, as taxation on production and land use often falls under state jurisdiction. The draft should clarify the constitutional basis for this tax and create a clear mechanism for revenue sharing with the states to avoid legal disputes. Without state cooperation, the implementation of this tax will be mired in legal battles.'),
(106, 9, 'In Agreement', 'As a tech company with a minimal carbon footprint, we fully support the carbon tax in Section 9. This policy will correctly incentivize a shift in investment from carbon-intensive old-economy sectors to modern, clean-tech industries like ours. It levels the playing field by making polluters pay for their negative externalities. This will accelerate the transition to a greener, technology-driven economy.'),
(108, 4, 'In Agreement', 'Mandatory ESG reporting is a vital tool for NGOs like ours. It provides us with the official, audited data we need to hold corporations accountable for their environmental promises and labor practices. Section 8 will bring a new era of corporate transparency and allow us to verify the claims companies make in their press releases. We strongly support its implementation without any dilution.'),
(109, 8, 'Suggest removal', 'Our company is already investing thousands of crores in green hydrogen and other renewable energy projects, driven by market demand and our own corporate strategy. The proposed carbon tax in Section 9 is an unnecessary and punitive measure that disincentivizes voluntary action. It is a blunt instrument that does not recognize the proactive steps being taken by responsible corporations. We advocate for a system of carbon credits and incentives, not a blanket tax.'),
(112, 8, 'Suggest modification', 'The proposed carbon tax in Section 9 should have a "carve-out" for export-oriented industries. If my products become more expensive due to this tax, I will no longer be competitive in the international market against countries that do not have such a tax. This will harm India''s exports. The tax should only be applicable to goods sold domestically, or the government must provide an equivalent duty drawback for exporters.');

"""


def setup_database():
    """
    Creates the database schema and populates it with initial data.
    """
    # Check if the database file already exists. If so, don't re-populate.
    db_exists = os.path.exists(DATABASE_FILE)
    if db_exists:
        print(f"Database file '{DATABASE_FILE}' already exists. Skipping creation and population.")
        # We will still connect to verify the schema is there.
    
    # Connect to the SQLite database. It will be created if it doesn't exist.
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # IMPORTANT: Enable foreign key constraint enforcement
        cursor.execute("PRAGMA foreign_keys = ON;")

        # --- Create Tables ---
        print("Creating database schema...")
        cursor.execute(CREATE_DRAFTS_TABLE)
        cursor.execute(CREATE_SECTIONS_TABLE)
        cursor.execute(CREATE_USERS_TABLE)
        cursor.execute(CREATE_SUBMISSIONS_TABLE)
        cursor.execute(CREATE_COMMENTS_TABLE)
        print("Schema created successfully.")

        # --- Populate Tables (only if the database is new) ---
        if not db_exists:
            print("Populating database with initial data...")
            # executescript is used to run multiple SQL statements at once
            cursor.executescript(INSERT_DATA)
            print("Data inserted successfully.")
        else:
            # Check if comments table is empty, if so, populate.
            cursor.execute("SELECT COUNT(*) FROM comments")
            comment_count = cursor.fetchone()[0]
            if comment_count == 0:
                print("Database tables are empty. Populating with initial data...")
                cursor.executescript(INSERT_DATA)
                print("Data inserted successfully.")
            else:
                print(f"Found {comment_count} comments already in the database. No new data was inserted.")


        # Commit the changes to the database file
        conn.commit()

        # --- Verification Step ---
        print("\nVerification:")
        cursor.execute("SELECT COUNT(*) FROM drafts")
        draft_count = cursor.fetchone()[0]
        print(f"- Found {draft_count} drafts.")

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"- Found {user_count} users.")
        
        cursor.execute("SELECT COUNT(*) FROM comments")
        comment_count = cursor.fetchone()[0]
        print(f"- Found {comment_count} comments.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        # Ensure the connection is closed no matter what
        if conn:
            conn.close()
            print("\nDatabase setup complete. Connection closed.")

if __name__ == '__main__':
    # This block runs when you execute the script directly
    setup_database()