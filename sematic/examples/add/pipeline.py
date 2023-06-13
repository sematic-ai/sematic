from typing import List

# Standard Library
import time

# Sematic
import sematic
from sematic.types import PromptResponse


@sematic.func
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    time.sleep(5)
    return a + b


@sematic.func
def add3(a: float, b: float, c: float) -> float:
    """
    Adds three numbers.
    """
    return add(add(a, b), c)


ARTICLE = """
MIAMI−The courtroom was hushed throughout the brief hearing.

Trump, who wore his standard red tie, white shirt and blue suit, sat hunched between his lawyers at the defense table, crossing and uncrossing his arms, but never spoke.

His lawyers, Christopher Kise and Todd Blanche, offered his plea and argued about conditions of pretrial release.

“We most certainly enter a plea of not guilty,” Blanche said.

Justice Department special counsel Jack Smith attended the hearing with a dozen other government lawyers.

The government argued Trump should have no contact with potential witnesses, but reached an agreement with the defense not to talk with witnesses about the case. Government lawyers will draw up a list of witnesses they don’t want Trump to talk to about the case.

Trump also agreed not to talk with his personal valet, Walt Nauta, who is his co-defendant, about the case. Trump brushed past Nauta without saying anything after the hearing ended.

Here's what we know:

Trump stops at Miami cafe Versailles after arraignment
Now that his arraignment is over, Trump is headed to Bedminster, N.J., for the first major fundraiser of 2024 presidential campaign. 

But he first made a pit stop at Versailles, a well-known Cuban restaurant in Miami.

Flanked by Walt Nauta, his longtime personal aide and fellow defendant, Trump greeted supporters just minutes after pleading not guilty to federal charges related to his alleged mishandling of classified documents.

Trump’s efforts to use his arrest for political gain will continue later tonight when he delivers public remarks on his indictment from his golf club in Bedminster.

-Miles J. Herszenhorn

Trump and DOJ special counsel Jack Smith meet in courtroom
Justice Department special counsel Jack Smith attended Trump’s arraignment and sat in the courtroom along with a dozen other government lawyers while Trump pleaded not guilty.

It marks the first time Smith and Trump have been in the same courtroom.

Attorney General Merrick Garland named Smith to oversee the multi-pronged investigation into Trump’s efforts to subvert the 2020 election and into the former president’s handling of hundreds of classified documents.

- Rachel Looker 

Chaos as motorcade departs courthouse
A man was tackled by authorities and placed under arrest after he attempted to run in front of Donald Trump’s motorcade as the former president departed the courthouse.

Dominic Santana, 61, held a sign outside the courthouse reading “Lock him up,” and was dressed in a striped prisoner’s outfit. Santana, who lives in Miami but is originally from Cuba, told reporters earlier in the day that while he could not show his "disdain for Cuban government he could for the U.S. government."

The motorcade proceeded without incident after Santana was tackled and detained by law enforcement officials. 

-Romina Ruiz-Goiriena and Miles J. Herszenhorn

Trump leaves federal court. What’s next?
Former President Donald Trump departed the Wilkie D. Ferguson Jr. United States Courthouse in Miami after pleading not guilty to 37 federal charges related to his alleged mishandling of classified documents seized from Mar-a-Lago.

He will now travel back to his golf club in Bedminster, N.J., where he will make public remarks addressing his indictment and arraignment. Later tonight, he will host the first major fundraiser of his 2024 presidential campaign at the golf club.

While it is still unclear when the next legal development in the case will occur, special counsel Jack Smith previously said that he will seek a “speedy trial.”

-Miles J. Herszenhorn

Trump faces other legal challenges beyond federal case
Trump faces a number of legal hurdles besides the federal classified-documents case as he campaigns again for the White House:

Trump faces trial in New York on 34 counts of falsifying business records for hush payments to women who claimed to have had sex with him. He pleaded not guilty.
Smith is also investigating potential election fraud from Trump’s attempt to overturn the results of the 2022 election.
In Georgia, Fulton County District Attorney Fani Willis is investigating potential election fraud because of Trump’s fake electors in that state and because of his call Jan. 2, 2021, asking state Secretary of State Brad Raffensperger to “find” enough votes to overturn the election results.
E. Jean Carroll won a $5 million civil verdict against Trump for sexual abuse and defamation over an encounter at a New York department store in the 1990s. Trump has appealed.
-Bart Jansen

Trump's future campaign schedule is mostly blank right now
Donald Trump renews his 2024 campaign almost immediately after his arraignment with a prime time speech on Tuesday - but his campaign schedule beyond that is pretty much blank.

Trump speaks at 8:15 p.m. from his Bedminster golf club in New Jersey, where he is also hosting a fundraiser that was planned before his indictment in Miami.

The future campaign rally schedule right now is blank, though Trump is scheduled to speak at a convention of anti-abortion activists to be held June 29-July 2 in Philadelphia.

−David Jackson

Donald Trump arrested in classified docs investigation
Former President Donald Trump leaves his Trump National Doral resort, Tuesday, June 13, 2023 in Doral, Fla. (AP Photo/Jim Rassol) ORG XMIT: FLJS102
Former President Donald Trump turned himself in Tuesday afternoon at a federal court in Miami after being indicted last week on 37 counts related to a classified documents investigation.

Trump faces federal criminal charges for illegally retaining the nation’s classified Defense secrets. He is also accused of obstructing justice.

The former president pleaded not guilty at the Wilkie D. Ferguson Jr. U.S. Courthouse in Miami and said on Truth Social his surrender marked one of the saddest days in the country, adding unsubstantiated claims he is the victim of political persecution.

- Candy Woodall

Was Trump handcuffed? 
It is unlikely.

Former President Donald Trump surrendered to authorities and went through the pretrial services before appearing in court today. But he did not have a mug shot taken and he probably wasn't placed in handcuffs.

Trump was, however, expected to have his fingerprints taken digitally. 

After Trump was indicted in New York in March, he was not handcuffed when he surrendered to authorities for his arraignment. That will likely remain the case when he shows up on Tuesday for his hearing in Miami.

-Miles J. Herszenhorn

Trump motorcade: Aides record trip to Miami courthouse
If you want to know what a Trump motorcade is like - even one en route to an arrest-and-arraignment - some campaign aides have you covered.

At least two aides - Chris LaCivita and Steven Cheung - posted video from the motorcade as it headed to the federal courthouse in Miami.

"President Trump on the way to fight the witch-hunt," Cheung said on Twitter.                                    

−David Jackson
"""

@sematic.func
def pipeline(a: float, b: float, c: float) -> List[PromptResponse]:
    """
    ## This is the docstring

    A trivial pipeline to showcase basic future encapsulation.

    This pipeline simply adds a bunch of numbers. It shows how functions can
    be arbitrarily nested.

    ### It supports markdown

    `pretty_cool`.
    """
    # sum1 = add(a, b)
    # sum2 = add(b, c)
    # sum3 = add(a, c)
    # return add3(sum1, sum2, sum3)
    return [
        PromptResponse(
            prompt="Something short",
            response="Something also short",
        ),
        PromptResponse(
            prompt=ARTICLE,
            response="Trump said he's not guilty.",
        ),
    ]
