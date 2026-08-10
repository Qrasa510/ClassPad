WINDOW_DATA = {
    "default": [
        {
            "type": "div",
            "props": {
                "tw": "flex flex-col w-full h-full bg-black text-white p-[6px] gap-[5px]",
                "children": [
                    {
                        "type": "div",
                        "props": {
                            "tw": "flex flex-row items-center justify-between h-[18px] shrink-0 px-[3px]",
                            "children": [
                                {
                                    "type": "span",
                                    "props": {
                                        "tw": "text-16-chillduansans font-bold leading-none",
                                        "children": "{{get inputData \"day\" default=\"SAT\"}} · {{get inputData \"date\" default=\"9月1日\"}} · {{get inputData \"weather\" default=\"☀ 31°C\"}}"
                                    }
                                },
                                {
                                    "type": "span",
                                    "props": {
                                        "tw": "text-14-chillduansans font-bold leading-none",
                                        "children": "{{get inputData \"time\" default=\"9:41 AM\"}}"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "div",
                        "props": {
                            "tw": "flex flex-row h-[98px] shrink-0 gap-[5px]",
                            "children": [
                                {
                                    "type": "div",
                                    "props": {
                                        "tw": "flex flex-col w-[200px] shrink-0 bg-white text-black rounded-[6px] p-[5px] overflow-hidden",
                                        "children": [
                                            {
                                                "type": "div",
                                                "props": {
                                                    "tw": "flex flex-row h-[16px] items-center justify-between gap-[6px]",
                                                    "children": [
                                                        {
                                                            "type": "span",
                                                            "props": {
                                                                "tw": "text-14-chillduansans font-bold leading-none",
                                                                "children": "{{get inputData \"period\" default=\"正在上课  第三节\"}}"
                                                            }
                                                        },
                                                        {
                                                            "type": "span",
                                                            "props": {
                                                                "tw": "text-14-chillduansans font-bold leading-none shrink-0",
                                                                "children": "{{get inputData \"teacher\" default=\"\"}}"
                                                            }
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "text-48-logoscunboundedsans leading-none mt-[-12px]",
                                                    "children": "{{get inputData \"course\" default=\"暂无课程\"}}"
                                                }
                                            },
                                            {
                                                "type": "div",
                                                "props": {
                                                    "tw": "w-full h-[8px] rounded-full bg-black/20 border border-black shrink-0 mt-[14px] overflow-hidden",
                                                    "children": [
                                                        {
                                                            "type": "div",
                                                            "props": {
                                                                "tw": "h-full rounded-l-full rounded-r-none bg-black",
                                                                "style": {
                                                                    "width": "{{get inputData \"progress\" default=\"0\"}}%"
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                "type": "div",
                                                "props": {
                                                    "tw": "flex flex-row items-center justify-between h-[13px] shrink-0 mt-[2px]",
                                                    "children": [
                                                        {
                                                            "type": "span",
                                                            "props": {
                                                                "tw": "text-14-chillduansans font-bold leading-none",
                                                                "children": "剩余 {{get inputData \"remaining\" default=\"0\"}} 分钟"
                                                            }
                                                        },
                                                        {
                                                            "type": "span",
                                                            "props": {
                                                                "tw": "text-14-chillduansans leading-none",
                                                                "children": "{{get inputData \"courseTime\" default=\"16:00 — 16:45\"}}"
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "type": "div",
                                    "props": {
                                        "tw": "flex flex-col flex-1 min-w-0 bg-white text-black rounded-[6px] p-[7px] overflow-hidden",
                                        "children": [
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "text-16-chillduansans font-bold leading-none",
                                                    "children": "今日剩余"
                                                }
                                            },
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "text-48-logoscunboundedsans font-bold leading-none mt-[-12px]",
                                                    "children": "{{get inputData \"todayRemaining\" default=\"0\"}}"
                                                }
                                            },
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "text-14-chillduansans font-bold leading-none",
                                                    "children": "节课程"
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "type": "div",
                        "props": {
                            "tw": "flex flex-row items-center justify-between h-[18px] shrink-0 px-[2px] py-[2px] overflow-hidden",
                            "children": [
                                {
                                    "type": "div",
                                    "props": {
                                        "tw": "flex flex-row items-center gap-[7px] min-w-0 overflow-hidden",
                                        "children": [
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "text-12-chillduansans font-bold py-[2px] shrink-0",
                                                    "children": "接下来"
                                                }
                                            },
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "text-14-chillduansans font-bold truncate",
                                                    "children": "{{get inputData \"nextSeries\" default=\"语 数 英\"}}"
                                                }
                                            },
                                            {
                                                "type": "span",
                                                "props": {
                                                    "tw": "flex items-center justify-center w-[16px] h-[16px] rounded-full bg-white text-black text-14-chillduansans pl-[2px] pb-[2px] font-bold shrink-0",
                                                    "style": {
                                                        "display": "{{get inputData \"hiddenDisplay\" default=\"none\"}}"
                                                    },
                                                    "children": "{{get inputData \"hidden\" default=\"\"}}"
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "type": "span",
                                    "props": {
                                        "tw": "text-12-chillduansans shrink-0",
                                        "children": "♙ {{get inputData \"owner\" default=\"Qrasa\"}}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    ]
}
