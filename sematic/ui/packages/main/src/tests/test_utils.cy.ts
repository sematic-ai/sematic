import { abbreviatedUserName, sha1, AsyncInvocationQueue } from "@sematic/main/src/utils";
import user from "@sematic/ui-test/fixtures/user";

describe('sha1', () => {
    it("should calculate sha1 value from string", async () => {
        expect(await sha1("localhost")).to.equal("334389048b872a533002b34d73f8c29fd09efc50");
        expect(await sha1("127.0.0.1")).to.equal("4b84b15bff6ee5796152495a230e45e3d7e947d9");
    });
});

describe('abbreviatedUserName()', () => {
    it("should generate abbreviated user name with User data", () => {
        expect(abbreviatedUserName(user)).to.equal("Grace H.");
    });
    it("should return empty string when the parameter is not provided", () => {
        expect(abbreviatedUserName(null)).to.equal("");
    });
});

describe('AsyncInvocationQueue', () => {
    it("should sequentialize function invocation using a queue", () => {
        let asyncFunction: any;
        let asyncController: AsyncInvocationQueue;
        cy.clock();
        cy.wait(0).then(async () => {
            asyncController = new AsyncInvocationQueue();
            asyncFunction = cy.spy(async () => {
                await new Promise(resolve => setTimeout(resolve, 100));
            });
        });
        cy.wait(0).then(async () => {
            setTimeout(async () => {
                const release = await asyncController.acquire();
                await asyncFunction();
                release();
            }, 0);
    
            setTimeout(async () => {
                const release = await asyncController.acquire();
                await asyncFunction();
                release();
            }, 20);
        });

        cy.tick(0); // trigger the first call
        cy.wait(0);
        cy.tick(20); // trigger the second call
        cy.wait(0);
        cy.tick(30).then(() => {
            // test that at 50th millisecond, the function is executed only once
            // because the second call is queued
            expect(asyncFunction).to.have.callCount(1);
            expect(asyncController.IsBusy).to.equal(true);
        });
        cy.wait(0);

        cy.tick(50); // this resolves the 1st call
        cy.wait(0);
        cy.tick(50); // this resolves the sleep in AsyncInvocationQueue
        cy.wait(0);
        cy.wait(0).then(() => {
            // test that at 150th millisecond, the function is executed twice
            expect(asyncFunction).to.have.callCount(2);
        });
        
    });
});