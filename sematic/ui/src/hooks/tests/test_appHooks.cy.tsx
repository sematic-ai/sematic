import { MemoryRouter } from "react-router-dom";
import {useAuthentication} from "../appHooks"

describe('useAutentication hook', () => {
    it("produces app context value if auth is not enabled", () => {
        cy.intercept(
            {
              method: 'GET',
              url: '/authenticate',
            },
            {
                "authenticate": false,
                "providers": {}
            }
          );
        
        let result: ReturnType<typeof useAuthentication> | undefined;

        function Wrapper() {
            result = useAuthentication();
            return <div data-cy={"result"}>{result.loading.toString()}</div>;
        }

        cy.mount(<MemoryRouter><Wrapper /></MemoryRouter>);
        cy.get("[data-cy=result]").should('have.text', 'true');
        
        cy.get("[data-cy=result]").should('have.text', 'false').then(() => {
            expect(result).to.eql({
                "isAuthenticationEnabled": false,
                "authProviderDetails": {},
                error: undefined,
                "loading": false
            });
        });
    });

    it("produces app context value if auth is enabled", () => {
        cy.intercept(
            {
              method: 'GET',
              url: '/authenticate',
            },
            {
                "authenticate": true,
                "providers": {
                  "GOOGLE_OAUTH_CLIENT_ID": "12345.apps.googleusercontent.com"
                }
              }
          );
        
        let result: ReturnType<typeof useAuthentication> | undefined;

        function Wrapper() {
            result = useAuthentication();
            return <div data-cy={"result"}>{result.loading.toString()}</div>;
        }

        cy.mount(<MemoryRouter><Wrapper /></MemoryRouter>);
        cy.get("[data-cy=result]").should('have.text', 'false').then(() => {
            expect(result).to.eql({
                "isAuthenticationEnabled": true,
                "authProviderDetails": {
                    "google": {
                        "GOOGLE_OAUTH_CLIENT_ID": "12345.apps.googleusercontent.com"
                    }
                },
                error: undefined,
                "loading": false
            });
        });
    });
});