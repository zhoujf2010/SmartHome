import { fireEvent } from "../../../common/dom/fire_event";
import { LovelaceCardConfig, LovelaceConfig } from "../../../data/lovelace";

export interface EditCardDialogParams {
  lovelaceConfig: LovelaceConfig;
  saveConfig: (config: LovelaceConfig) => void;
  path: [number] | [number, number];
  cardConfig?: LovelaceCardConfig;
}

//TODO
export const importEditCardDialog = () => {};//import("./hui-dialog-edit-card");

export const showEditCardDialog = (
  element: HTMLElement,
  editCardDialogParams: EditCardDialogParams
): void => {
  // @ts-ignore: Unreachable code error
  fireEvent(element, "show-dialog", {
    dialogTag: "hui-dialog-edit-card",
    dialogImport: importEditCardDialog,
    dialogParams: editCardDialogParams,
  });
};
