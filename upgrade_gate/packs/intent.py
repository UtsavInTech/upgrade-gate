"""intent: customer-support (banking) intent classification, en + hinglish.

Own labelled set written from templates (no external download). Each intent has 8 templates
written in both English and Hinglish (the paired items share fillers, prefix and suffix) plus
5 English-only templates. A public set such as Banking77 could replace this later.
"""
from __future__ import annotations

from typing import List

from ..schema import Task
from ._common import CITIES, NAMES, fmt_inr, rng_for

PACK = "intent"
EN_PER_INTENT = 17
HG_PER_INTENT = 8

# intent -> (paired [(en, hinglish)], english-only [en])
INTENTS = {
    "card_lost": ([
        ("I lost my debit card somewhere in the market today.", "Mera debit card aaj market mein kahin gir gaya."),
        ("My wallet was stolen and my credit card was in it.", "Mera wallet chori ho gaya, credit card bhi usi mein tha."),
        ("I can't find my card anywhere, please block it.", "Mera card kahin mil nahi raha, please block kar do."),
        ("Someone stole my card ending {last4} on the train.", "Train mein kisi ne mera {last4} wala card chura liya."),
        ("I think I left my card at a restaurant last night and now it's gone.", "Lagta hai kal raat card restaurant mein chhoot gaya, ab mil nahi raha."),
        ("Please block my ATM card immediately, I have lost it.", "Mera ATM card kho gaya hai, turant block karo."),
        ("My purse got snatched and both my cards were inside.", "Kisi ne mera purse chheen liya, dono cards usmein the."),
        ("I dropped my card somewhere between home and office.", "Ghar aur office ke beech kahin mera card gir gaya."),
    ], [
        "Lost my card while travelling to {city}, need to report it.",
        "How do I report a missing credit card?",
        "My debit card has been missing since yesterday.",
        "I misplaced my card and I'm worried someone will use it.",
        "Report card ending {last4} as stolen.",
    ]),
    "card_declined": ([
        ("My card got declined at the supermarket even though I have money.", "Supermarket mein mera card decline ho gaya jabki account mein paise hain."),
        ("Why is my debit card not working for online payments?", "Mera debit card online payment ke liye kaam kyun nahi kar raha?"),
        ("The shop's card machine keeps rejecting my card.", "Dukaan ki machine baar baar mera card reject kar rahi hai."),
        ("My card ending {last4} was refused at the petrol pump.", "Petrol pump pe mera {last4} wala card refuse ho gaya."),
        ("Every time I swipe my card it says transaction declined.", "Jab bhi card swipe karte hain, transaction declined aata hai."),
        ("I tried paying {amount} at {merchant} but my card was declined.", "{merchant} pe {amount} pay karne ki koshish ki par card decline ho gaya."),
        ("My credit card isn't being accepted anywhere since this morning.", "Subah se mera credit card kahin bhi accept nahi ho raha."),
        ("Card payment failed at the restaurant, the waiter said it was declined.", "Restaurant mein card payment fail ho gaya, waiter ne bola declined hai."),
    ], [
        "Why does my card keep getting declined at shops?",
        "My card works at ATMs but not at stores, why?",
        "My card was rejected when I tried to book a train ticket.",
        "My card was declined twice today, is something wrong with it?",
        "Card declined at checkout on {merchant}, please check.",
    ]),
    "refund_request": ([
        ("I returned the shoes to {merchant} but haven't got my refund of {amount}.", "Maine {merchant} ko shoes return kar diye par {amount} ka refund nahi mila."),
        ("I cancelled my order, when will my money be refunded?", "Order cancel kar diya, paise kab refund honge?"),
        ("Please refund the {amount} for the product I sent back.", "Jo product wapas bheja uska {amount} refund kar do please."),
        ("The seller agreed to refund me but nothing has come yet.", "Seller ne refund ka bola tha par abhi tak kuch nahi aaya."),
        ("I want my money back for a cancelled flight ticket.", "Cancel hui flight ticket ke paise wapas chahiye."),
        ("It's been {days} days since my return was picked up and still no refund.", "Return pickup hue {days} din ho gaye, refund ab tak nahi aaya."),
        ("How long does a refund to my card usually take?", "Card pe refund aane mein kitna time lagta hai?"),
        ("My hotel booking was cancelled, I need the {amount} returned.", "Hotel booking cancel ho gayi, mujhe {amount} wapas chahiye."),
    ], [
        "Where is my refund for the order I cancelled last week?",
        "The merchant says the refund was processed but I don't see it.",
        "Can you help me get a refund from {merchant}?",
        "I need to claim back money for an item I returned.",
        "I cancelled my gym membership, I want the {amount} refunded.",
    ]),
    "balance_inquiry": ([
        ("What is my current account balance?", "Mera current account balance kitna hai?"),
        ("How much money is left in my savings account?", "Savings account mein kitne paise bache hain?"),
        ("Can you tell me my balance please?", "Mera balance bata do please."),
        ("I want to check how much I have before paying rent.", "Rent dene se pehle check karna hai ki kitna balance hai."),
        ("Show me the available balance in my account ending {last4}.", "{last4} wale account ka available balance dikhao."),
        ("Has my salary been credited? What's the balance now?", "Salary aayi kya? Ab balance kitna hai?"),
        ("How do I check my balance on the app?", "App pe balance kaise check karein?"),
        ("Do I have at least {amount} in my account?", "Kya mere account mein kam se kam {amount} hain?"),
    ], [
        "Balance enquiry for my savings account.",
        "How much money is in my account right now?",
        "I'd like to know my remaining balance after today's purchases.",
        "Please send me my account balance by SMS.",
        "How much can I spend right now? Check my balance.",
    ]),
    "transfer_failed": ([
        ("I sent {amount} to {name} but the transfer failed and the money was deducted.", "Maine {name} ko {amount} bheje, transfer fail ho gaya aur paise kat gaye."),
        ("My UPI payment shows failed but the amount left my account.", "Mera UPI payment failed dikha raha hai par paise account se chale gaye."),
        ("The bank transfer to my landlord didn't go through.", "Landlord ko bank transfer nahi gaya."),
        ("My NEFT transfer has been pending for {days} days.", "Mera NEFT transfer {days} din se pending hai."),
        ("My brother says he never received the money I transferred yesterday.", "Bhai keh raha hai jo paise maine kal transfer kiye woh use mile hi nahi."),
        ("Transfer error: the money was debited but not credited to the receiver.", "Transfer error: paise debit ho gaye par receiver ko credit nahi hue."),
        ("Why did my fund transfer of {amount} fail?", "Mera {amount} ka fund transfer fail kyun hua?"),
        ("I tried to send money abroad and it bounced back with an error.", "Bahar paise bhejne ki koshish ki, error aakar wapas aa gaye."),
    ], [
        "IMPS transfer unsuccessful but account debited.",
        "The payment to {name} is stuck, it neither failed nor completed.",
        "My transfer was rejected, what went wrong?",
        "A transfer I made this morning failed, when will I get the money back?",
        "Online transfer to my mother's account failed twice.",
    ]),
    "change_address": ([
        ("We have moved to {city}, please update my address.", "Hum {city} shift ho gaye hain, mera address update kar do."),
        ("How do I change the address on my account?", "Account pe address kaise change karein?"),
        ("I need to update my postal address for statements.", "Statements ke liye mera postal address update karna hai."),
        ("Please change my residential address to my new flat.", "Mera residential address naye flat ka kar do please."),
        ("My address in your records is old, I want to correct it.", "Aapke record mein mera purana address hai, use theek karna hai."),
        ("Can I update my address online or do I need to visit the branch?", "Address online update ho sakta hai ya branch jaana padega?"),
        ("We shifted house last month, my mail should go to the new address.", "Pichle mahine ghar shift kiya, ab letters naye address pe aane chahiye."),
        ("Update my communication address to {city}.", "Mera communication address {city} ka kar do."),
    ], [
        "Change of address request.",
        "I'm relocating to {city} next week; what documents do I need to change my address?",
        "My permanent address has changed, how do I update it?",
        "Wrong address on my account, please fix it.",
        "I want my bank letters sent to my office address instead.",
    ]),
    "reset_pin": ([
        ("I forgot my ATM PIN, how can I reset it?", "Mera ATM PIN yaad nahi aa raha, reset kaise karein?"),
        ("I want to change my debit card PIN.", "Mujhe debit card ka PIN change karna hai."),
        ("I entered the wrong PIN too many times, how do I set a new one?", "Bahut baar galat PIN daal diya, naya PIN kaise set karein?"),
        ("How do I generate a new PIN for my credit card?", "Credit card ka naya PIN kaise generate karein?"),
        ("Please help me reset the PIN for card ending {last4}.", "{last4} wale card ka PIN reset karne mein help karo."),
        ("Can I set my card PIN from the mobile app?", "Kya mobile app se card ka PIN set kar sakte hain?"),
        ("I think someone saw my PIN, I want to change it.", "Lagta hai kisi ne mera PIN dekh liya, change karna hai."),
        ("My PIN isn't working anymore, I need to reset it.", "Mera PIN ab kaam nahi kar raha, reset karna hai."),
    ], [
        "Reset ATM PIN.",
        "What's the process to change my card PIN at an ATM?",
        "I don't remember my PIN at all.",
        "I need a fresh PIN for my debit card.",
        "Can you send me a PIN reset link?",
    ]),
    "activate_card": ([
        ("I just received my new debit card, how do I activate it?", "Naya debit card mil gaya, activate kaise karein?"),
        ("Please activate the replacement card you sent me.", "Jo replacement card bheja tha use activate kar do."),
        ("My new credit card arrived today and isn't active yet.", "Naya credit card aaj aaya, abhi tak active nahi hai."),
        ("How can I start using the card that came in the post?", "Post se jo card aaya use use karna kaise shuru karein?"),
        ("Activate my card ending {last4}.", "{last4} wala card activate karo."),
        ("Do I need to activate my renewed card before using it?", "Renew hua card use karne se pehle activate karna padega kya?"),
        ("The courier delivered my card, what are the steps to enable it?", "Courier se card aa gaya, ise enable karne ke steps kya hain?"),
        ("I want to activate my new card for international use.", "Naye card ko international use ke liye activate karna hai."),
    ], [
        "Card activation please.",
        "New card received, I need it switched on.",
        "Is my new card activated already or do I have to do it?",
        "How long does it take for a new card to become active?",
        "I got my card in the mail yesterday; how do I activate it in the app?",
    ]),
    "account_statement": ([
        ("Please send me my bank statement for the last {months} months.", "Pichle {months} mahine ka bank statement bhej do."),
        ("I need an account statement for my visa application.", "Visa application ke liye account statement chahiye."),
        ("How do I download my statement as a PDF?", "Statement PDF mein kaise download karein?"),
        ("Can I get a stamped statement for my loan papers?", "Loan papers ke liye stamp wala statement mil sakta hai?"),
        ("Email me the statement for last month.", "Pichle mahine ka statement email kar do."),
        ("I want a statement of all transactions from last year.", "Pichle saal ke saare transactions ka statement chahiye."),
        ("My monthly e-statement didn't arrive this time.", "Is baar monthly e-statement nahi aaya."),
        ("Generate a statement for account ending {last4}.", "{last4} wale account ka statement nikal do."),
    ], [
        "Statement request for tax filing.",
        "I need a printed statement for the last quarter.",
        "Where can I find my previous statements online?",
        "Kindly share my credit card statement for this billing cycle.",
        "Account statement from April to September, please.",
    ]),
    "unrecognized_transaction": ([
        ("There is a charge of {amount} on my card that I didn't make.", "Mere card pe {amount} ka charge hai jo maine kiya hi nahi."),
        ("I see a payment to {merchant} that I don't recognise.", "{merchant} ko ek payment dikh rahi hai jiske baare mein mujhe kuch pata nahi."),
        ("Someone has used my card online without my permission.", "Kisi ne bina permission mera card online use kar liya."),
        ("Money was debited from my account and I have no idea why.", "Account se paise kat gaye aur mujhe pata nahi kyun."),
        ("I got an SMS for a {amount} transaction I never did.", "{amount} ke transaction ka SMS aaya jo maine kabhi kiya hi nahi."),
        ("There are three unknown transactions on my statement.", "Mere statement mein teen anjaan transactions hain."),
        ("I think my card has been cloned, there are strange charges.", "Lagta hai mera card clone ho gaya, ajeeb charges aa rahe hain."),
        ("A transaction from another city appeared while my card was with me.", "Card mere paas tha phir bhi doosre shehar ka transaction aa gaya."),
    ], [
        "Fraudulent charge on my credit card, please investigate.",
        "Unauthorised debit of {amount} this morning.",
        "I want to dispute a transaction I did not authorise.",
        "Who is {merchant}? They charged my card and I never bought anything there.",
        "My account shows a withdrawal I didn't do.",
    ]),
    "close_account": ([
        ("I want to close my savings account.", "Mujhe apna savings account band karna hai."),
        ("How do I shut down my account permanently?", "Account permanently band kaise karein?"),
        ("Please close my account and transfer the balance to my other bank.", "Mera account close karke balance doosre bank mein bhej do."),
        ("I'm moving abroad and need to close my account.", "Videsh shift hona hai, isliye account close karna hai."),
        ("What's the procedure to close a joint account?", "Joint account close karne ka process kya hai?"),
        ("I no longer need this account, please close it.", "Ab is account ki zarurat nahi, ise band kar do."),
        ("Is there a charge for closing my account?", "Account close karne ka koi charge hai kya?"),
        ("Close account ending {last4}.", "{last4} wala account close karo."),
    ], [
        "Account closure request.",
        "I want to end my relationship with the bank and close everything.",
        "Can I close my account online without visiting the branch?",
        "Please close my salary account, I've changed jobs.",
        "Help me close the account I opened last year.",
    ]),
    "update_phone_number": ([
        ("I changed my mobile number, please update it in my account.", "Maine mobile number badal liya, account mein update kar do."),
        ("How do I link a new phone number to my bank account?", "Naya phone number bank account se kaise link karein?"),
        ("I'm not getting OTPs because my registered number is old.", "OTP nahi aa raha kyunki registered number purana hai."),
        ("Please replace my registered mobile with a new number.", "Mera registered mobile naye number se replace kar do."),
        ("My old SIM is lost, I want to update my number.", "Purani SIM kho gayi, number update karna hai."),
        ("Can I change my contact number through the app?", "Kya app se contact number change ho sakta hai?"),
        ("Update my mobile number to the one ending {last4}.", "Mera mobile number {last4} wale number pe update karo."),
        ("SMS alerts go to my old phone, I want them on my new number.", "SMS alerts purane phone pe jaate hain, naye number pe chahiye."),
    ], [
        "Change registered mobile number.",
        "I have a new phone number and need to update my details.",
        "What documents are needed to change my phone number with the bank?",
        "Please update my contact number, the old one is disconnected.",
        "How long does it take for a mobile number change to reflect?",
    ]),
    "cash_withdrawal_failed": ([
        ("The ATM didn't give me cash but my account was debited {amount}.", "ATM se cash nahi nikla par account se {amount} kat gaye."),
        ("I tried to withdraw money and the machine showed an error, but the money is gone.", "Paise nikalne ki koshish ki, machine ne error dikhaya, par paise kat gaye."),
        ("ATM withdrawal failed, but the amount still got deducted.", "ATM withdrawal fail hua, phir bhi amount deduct ho gaya."),
        ("Only part of the cash came out of the ATM.", "ATM se sirf aadha cash nikla."),
        ("The ATM in {city} debited me without dispensing any notes.", "{city} ke ATM ne paise kaat liye par note nahi diye."),
        ("No cash came out but I got a debit SMS for {amount}.", "Cash nahi aaya par {amount} ka debit SMS aa gaya."),
        ("When will I get back the money from a failed ATM withdrawal?", "Failed ATM withdrawal ke paise kab wapas aayenge?"),
        ("The ATM screen froze during withdrawal and money was debited.", "Withdrawal ke time ATM screen hang ho gayi aur paise debit ho gaye."),
    ], [
        "Cash not dispensed at ATM, please reverse the debit.",
        "I withdrew {amount} at the ATM but received nothing.",
        "ATM transaction failed but my balance went down.",
        "The machine counted the notes but never released them.",
        "Failed cash withdrawal at another bank's ATM, money deducted.",
    ]),
    "exchange_rate": ([
        ("What is today's exchange rate for US dollars?", "Aaj US dollar ka exchange rate kya hai?"),
        ("How many rupees will I get for 100 euros?", "100 euro ke kitne rupaye milenge?"),
        ("What rate do you use to convert my card payments abroad?", "Bahar card payment convert karne ke liye aap kaunsa rate lagate ho?"),
        ("I'm travelling to Dubai, what's the dirham rate today?", "Dubai jaana hai, aaj dirham ka rate kya hai?"),
        ("Is the forex rate better in the app or at the branch?", "Forex rate app mein better hai ya branch mein?"),
        ("Tell me the current pound to rupee rate.", "Abhi pound to rupee rate batao."),
        ("Why was I charged a different exchange rate than the one shown online?", "Online jo rate dikha usse alag exchange rate kyun laga?"),
        ("What conversion rate applies if I buy Canadian dollars today?", "Aaj Canadian dollar khareedne pe conversion rate kya lagega?"),
    ], [
        "Exchange rate for Singapore dollars, please.",
        "How much is one US dollar in rupees today?",
        "Do you add a markup on the currency exchange rate?",
        "What is the current yen rate?",
        "What's your buying rate for euros today?",
    ]),
    "order_cheque_book": ([
        ("I need a new cheque book.", "Mujhe nayi cheque book chahiye."),
        ("How do I request a cheque book online?", "Cheque book online kaise request karein?"),
        ("My cheque leaves are finished, please send another book.", "Cheque ke saare panne khatam ho gaye, doosri book bhej do."),
        ("Can you deliver a cheque book to my home address?", "Cheque book ghar ke address pe bhej sakte ho?"),
        ("Please issue a 25-leaf cheque book for my current account.", "Current account ke liye 25 pannon wali cheque book issue kar do."),
        ("I ordered a cheque book {days} days ago, where is it?", "{days} din pehle cheque book order ki thi, kahan hai?"),
        ("Is there a fee for a new cheque book?", "Nayi cheque book ki koi fees hai kya?"),
        ("Order a cheque book for account ending {last4}.", "{last4} wale account ke liye cheque book order karo."),
    ], [
        "Cheque book request.",
        "Send me a fresh chequebook please.",
        "How many days does it take to receive a cheque book?",
        "I want to apply for a cheque book through net banking.",
        "I need cheques for paying my rent, please arrange a book.",
    ]),
}

LABELS = sorted(INTENTS)
MERCHANTS = ["ShopKart", "QuickMart", "TrendBazaar", "FoodDash", "TravelNest", "Zesto Foods", "UrbanCart"]
PREFIX = [("", ""), ("Hi, ", "Hi, "), ("Hello, ", "Hello, "), ("Urgent: ", "Urgent: ")]
SUFFIX = [("", ""), (" Please help.", " Please help karo."), (" Thanks.", " Thanks."), (" Please reply soon.", " Jaldi reply karo.")]

KEEP_CASE = ("I ", "I'", "ATM", "UPI", "NEFT", "IMPS", "PIN", "SMS", "OTP", "{", "US ", "Dubai")


def _apply(tmpl: str, f: dict, pre: str, suf: str) -> str:
    text = tmpl.format(**f)
    if pre and not tmpl.startswith(KEEP_CASE) and not text[0].isdigit():
        text = text[0].lower() + text[1:]
    return pre + text + suf


def _fill(r):
    return {
        "amount": "₹" + fmt_inr(r.choice([199, 450, 999, 1250, 2500, 3999, 5000, 7800, 12000, 15499])),
        "merchant": r.choice(MERCHANTS),
        "days": r.randint(3, 20),
        "months": r.choice([3, 6, 12]),
        "last4": "%04d" % r.randint(0, 9999),
        "city": r.choice(CITIES)[0],
        "name": r.choice(NAMES)[0].split()[0],
    }


PROMPT = {
    "en": "Classify the customer message into exactly one of these intents: %s. Reply with only the intent label.\n\nMessage: %s",
    "hinglish": "Is customer message ko in intents mein se exactly ek mein classify karo: %s. Sirf intent label likho.\n\nMessage: %s",
}


def build() -> List[Task]:
    r = rng_for(PACK)
    labels_s = ", ".join(LABELS)
    tasks: List[Task] = []
    idx = 0
    for label in LABELS:
        paired, en_only = INTENTS[label]
        seen = set()
        # 1) paired items (English + Hinglish share fillers, prefix, suffix)
        for en_t, hg_t in paired:
            f = _fill(r)
            p = r.randrange(len(PREFIX))
            s = r.randrange(len(SUFFIX))
            en = _apply(en_t, f, PREFIX[p][0], SUFFIX[s][0])
            hg = _apply(hg_t, f, PREFIX[p][1], SUFFIX[s][1])
            idx += 1
            en_id = "%s-%04d-en" % (PACK, idx)
            seen.add(en)
            for lang, msg in (("en", en), ("hinglish", hg)):
                tasks.append(_task(idx, lang, label, labels_s, msg, None if lang == "en" else en_id, en_id, "paired"))
        # 2) English-only extras: en-only templates, then re-fills of paired templates
        extra_templates = list(en_only) + [t for t, _ in paired if "{" in t] + [t for t, _ in paired if "{" not in t]
        k = 0
        n_en = len(paired)
        while n_en < EN_PER_INTENT:
            tmpl = extra_templates[k % len(extra_templates)]
            k += 1
            f = _fill(r)
            p = r.randrange(len(PREFIX))
            s = r.randrange(len(SUFFIX))
            if k > len(en_only) and p == 0 and s == 0:
                p = 1 + (k % 3)  # re-used template: force a different surface form
            en = _apply(tmpl, f, PREFIX[p][0], SUFFIX[s][0])
            if en in seen:
                continue
            seen.add(en)
            idx += 1
            tasks.append(_task(idx, "en", label, labels_s, en, None, "%s-%04d-en" % (PACK, idx), "en_only"))
            n_en += 1
    return tasks


def _task(idx, lang, label, labels_s, msg, pair_id, group, kind) -> Task:
    return Task(
        id="%s-%04d-%s" % (PACK, idx, lang), pack=PACK, category="classification", lang=lang, modality="text",
        prompt=PROMPT[lang] % (labels_s, msg), reference=label,
        scorer={"type": "label", "value": label, "labels": list(LABELS)},
        pair_id=pair_id, meta={"group": group, "message": msg, "kind": kind},
    )
