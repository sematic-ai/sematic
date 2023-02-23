import { useQueuedAsyncRetry } from '../helperHooks';

describe('useQueuedAsyncRetry hook', () => {
  it("should queue retry request while previous loading hasn't finished", () => {
    let retry: () => void;

    const mockedAsyncFunc = cy.spy(async () => {
      await new Promise((resolve) => {
        setTimeout(resolve, 100);
      });
    });

    const TestComponent = () => {
      const result = useQueuedAsyncRetry(mockedAsyncFunc);
      const loading = result.loading;
      retry = result.retry;
      return <div data-cy={"result"}>{loading.toString()}</div>;
    }
    
    cy.clock();
    cy.mount(<TestComponent />);
    
    cy.wait(0).then(() => {
      cy.get("[data-cy=result]").should('have.text', 'true');
      expect(mockedAsyncFunc).to.have.callCount(1);
    });

    cy.tick(50);
    cy.wait(0).then(() => {
      // Call `retry` before loading is resolved.
      retry();

      cy.get("[data-cy=result]").should('have.text', 'true');
    });
    cy.tick(51);
    
    cy.wait(0).then(() => {
      // at 101st milliseconds, the async function will be called the 2nd time
      // and loading state is `true`.
      cy.get("[data-cy=result]").should('have.text', 'true');
    });
    cy.wait(0); // yield to react rendering
    cy.tick(100);

    cy.wait(0).then(() => {
      // at 201st milliseconds, the 2nd call to the async function will complete
      // and loading state is `false`.
      cy.get("[data-cy=result]").should('have.text', 'false');
      expect(mockedAsyncFunc).to.have.callCount(2);
    });
  })
})