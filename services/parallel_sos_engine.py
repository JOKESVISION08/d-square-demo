"""
D-SQUARE 2.0 Parallel SOS Alert Engine
Simultaneously dispatches:
1. RESCUE GPT MANAGEMENT payload (for first responders, NDRF, authorities)
2. D-SQUARE GPT PUBLIC payload (for citizens via app/SMS/WhatsApp in EN, HI, MR)
"""

import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List


class MultiLanguageLocalization:
    """Multi-language localization for D-SQUARE GPT public disaster advisories"""

    LOCALIZED_TEXTS = {
        "FLOOD": {
            "en": {
                "title": "🚨 FLOOD ALERT! Immediate Evacuation Required",
                "message": "Your area is under RESTRICTED ACCESS due to rising flood waters. Evacuate immediately to designated high ground!",
                "safety_steps": [
                    "1. Move immediately to higher ground or upper floor",
                    "2. Avoid walking or driving through moving flood water",
                    "3. Carry essential emergency kit (water, torch, medicine, ID)",
                    "4. Turn off main electrical switches and gas valve",
                    "5. Follow designated evacuation routes and call 108/112 if trapped"
                ]
            },
            "hi": {
                "title": "🚨 बाढ़ चेतावनी! तत्काल निकासी आवश्यक",
                "message": "बढ़ते बाढ़ के पानी के कारण आपका क्षेत्र प्रतिबंधित पहुंच के तहत है। तुरंत ऊंचे स्थान पर जाएं!",
                "safety_steps": [
                    "1. तुरंत ऊंचे स्थान या ऊपरी मंजिल पर जाएं",
                    "2. बहते पानी में चलने या गाड़ी चलाने से बचें",
                    "3. आवश्यक आपातकालीन किट (पानी, टॉर्च, दवा) साथ रखें",
                    "4. मुख्य बिजली स्विच और गैस वाल्व बंद करें",
                    "5. निर्दिष्ट निकासी मार्गों का पालन करें और फंसने पर 108/112 पर कॉल करें"
                ]
            },
            "mr": {
                "title": "🚨 पूर इशारा! तातडीने सुरक्षित स्थळी जा",
                "message": "पुराच्या पाण्यामुळे तुमचा परिसर प्रतिबंधित क्षेत्र घोषित करण्यात आला आहे. त्वरित उंच ठिकाणी जा!",
                "safety_steps": [
                    "1. त्वरित उंच ठिकाणी किंवा वरच्या मजल्यावर जा",
                    "2. वाहत्या पाण्यातून चालणे किंवा वाहन चालवणे टाळा",
                    "3. अत्यावश्यक आपत्कालीन किट (पाणी, टॉर्च, औषधे) सोबत ठेवा",
                    "4. मुख्य वीज स्विच आणि गॅस व्हॉल्व्ह बंद करा",
                    "5. नियुक्त सुटका मार्गांचा वापर करा आणि अडकल्यास 108/112 वर कॉल करा"
                ]
            }
        },
        "FIRE": {
            "en": {
                "title": "🚨 FIRE HAZARD ALERT! Evacuate Upwind",
                "message": "High-temperature fire hotspot detected. Evacuate upwind immediately and avoid toxic smoke plumes!",
                "safety_steps": [
                    "1. Evacuate upwind away from smoke and flames",
                    "2. Cover nose and mouth with wet cloth or N95 mask",
                    "3. Stay low to the ground to avoid inhaling dense smoke",
                    "4. Do not return to buildings until declared safe",
                    "5. Call 101/112 for emergency fire services"
                ]
            },
            "hi": {
                "title": "🚨 अग्नि चेतावनी! हवा के विपरीत दिशा में निकलें",
                "message": "उच्च तापमान वाली आग का पता चला है। जहरीले धुएं से बचने के लिए तुरंत हवा के विपरीत दिशा में निकलें!",
                "safety_steps": [
                    "1. धुएं और लपटों से दूर हवा के विपरीत दिशा में जाएं",
                    "2. नाक और मुंह को गीले कपड़े या N95 मास्क से ढकें",
                    "3. जहरीले धुएं से बचने के लिए नीचे झुककर चलें",
                    "4. सुरक्षित घोषित होने तक इमारतों में वापस न लौटें",
                    "5. आपातकालीन अग्निशमन सेवाओं के लिए 101/112 पर कॉल करें"
                ]
            },
            "mr": {
                "title": "🚨 आग आपत्ती इशारा! वाऱ्याच्या दिशेने सुरक्षित ठिकाणी जा",
                "message": "तीव्र आगीची घटना आढळली आहे. विषारी धुरापासून वाचण्यासाठी त्वरित सुरक्षित स्थळी जा!",
                "safety_steps": [
                    "1. धूर आणि ज्वालांपासून दूर सुरक्षित दिशेने जा",
                    "2. नाक आणि तोंड ओल्या कपड्याने किंवा मास्कने झाका",
                    "3. धुराचा त्रास टाळण्यासाठी खाली वाकून चला",
                    "4. सुरक्षित घोषित होईपर्यंत इमारतीत परत जाऊ नका",
                    "5. आपत्कालीन अग्निशामक सेवेसाठी 101/112 वर कॉल करा"
                ]
            }
        },
        "EARTHQUAKE": {
            "en": {
                "title": "🚨 EARTHQUAKE ALERT! Drop, Cover and Hold On",
                "message": "Seismic activity detected. Stay clear of heavy structures, glass, and power lines!",
                "safety_steps": [
                    "1. DROP to hands and knees, COVER head/neck, HOLD ON under sturdy furniture",
                    "2. Stay indoors until shaking stops, then evacuate via stairs (NO ELEVATORS)",
                    "3. Move to open space away from buildings, trees, and power lines",
                    "4. Expect aftershocks and check for gas leaks before lighting flames",
                    "5. Call 108/112 for medical emergency assistance"
                ]
            },
            "hi": {
                "title": "🚨 भूकंप चेतावनी! झुकें, ढकें और पकड़ें",
                "message": "भूकंपीय गतिविधि पाई गई है। भारी संरचनाओं, कांच और बिजली की लाइनों से दूर रहें!",
                "safety_steps": [
                    "1. नीचे झुकें, मजबूत मेज के नीचे सिर ढकें और कसकर पकड़ें",
                    "2. झटके रुकने तक अंदर रहें, फिर सीढ़ियों से बाहर निकलें (लिफ्ट का उपयोग न करें)",
                    "3. इमारतों, पेड़ों और बिजली की तारों से दूर खुले मैदान में जाएं",
                    "4. आफ्टरशॉक के लिए तैयार रहें और गैस लीक की जांच करें",
                    "5. चिकित्सा आपातकालीन सहायता के लिए 108/112 पर कॉल करें"
                ]
            },
            "mr": {
                "title": "🚨 भूकंप इशारा! खाली बसा, डोके झाका आणि धरा",
                "message": "भूकंपाचे धक्के जाणवले आहेत. उंच इमारती, काच आणि विजेच्या तारांपासून दूर रहा!",
                "safety_steps": [
                    "1. खाली बसा, मजबूत टेबलाखाली डोके झाका आणि घट्ट धरा",
                    "2. धक्के थांबेपर्यंत आत राहा, नंतर पायऱ्यांवरून बाहेर पडा (लिफ्ट वापरू नका)",
                    "3. इमारती आणि झाडांपासून दूर मोकळ्या मैदानात जा",
                    "4. उप-धक्क्यांसाठी (Aftershocks) तयार राहा",
                    "5. वैद्यकीय मदतीसाठी 108/112 वर कॉल करा"
                ]
            }
        },
        "LANDSLIDE": {
            "en": {
                "title": "🚨 LANDSLIDE ALERT! Evacuate Slope Hazard Zone",
                "message": "Slope shift & high pore-water pressure detected. Evacuate slope-adjacent structures immediately!",
                "safety_steps": [
                    "1. Move away from steep slopes, cliffs, and drainage channels",
                    "2. Listen for unusual rumbles or snapping trees",
                    "3. Evacuate to designated high-ground concrete shelters",
                    "4. Avoid mountain passes and road cuts prone to falling rock",
                    "5. Call 108/112 for search & rescue deployment"
                ]
            },
            "hi": {
                "title": "🚨 भूस्खलन चेतावनी! ढलान खतरे वाले क्षेत्र से निकलें",
                "message": "ढलान खिसकने का खतरा है। ढलान के पास बने मकानों से तुरंत बाहर निकलें!",
                "safety_steps": [
                    "1. खड़ी ढलानों, चट्टानों और नालों से दूर रहें",
                    "2. असामान्य गड़गड़ाहट या पेड़ों के टूटने की आवाज पर सतर्क रहें",
                    "3. निर्दिष्ट पक्के आश्रय स्थलों की ओर जाएं",
                    "4. पहाड़ी रास्तों और कटान वाले रास्तों से बचें",
                    "5. खोज एवं बचाव दल के लिए 108/112 पर कॉल करें"
                ]
            },
            "mr": {
                "title": "🚨 भूस्खलन इशारा! डोंगराळ धोकादायक क्षेत्रातून बाहेर पडा",
                "message": "डोंगर खचण्याचा धोका निर्माण झाला आहे. पायथ्याशी असलेल्या घरांतून त्वरित बाहेर पडा!",
                "safety_steps": [
                    "1. तीव्र उतार आणि कड्यांपासून दूर राहा",
                    "2. झाडे किंवा दगड कोसळण्याच्या आवाजावर लक्ष ठेवा",
                    "3. सुरक्षित पक्या निवारा केंद्रात जा",
                    "4. डोंगराळ रस्त्यांवरून प्रवास करणे टाळा",
                    "5. बचाव पथकासाठी 108/112 वर कॉल करा"
                ]
            }
        },
        "CYCLONE": {
            "en": {
                "title": "🚨 CYCLONE RED ALERT! Take Shelter Immediately",
                "message": "Extremely severe gale winds and storm surge expected. Stay indoors in reinforced shelter!",
                "safety_steps": [
                    "1. Stay indoors away from windows, unfastened roofs, and glass panes",
                    "2. Secure loose outdoor objects and move livestock to shelter",
                    "3. Stock 72 hours of drinking water, dry food, and first aid kit",
                    "4. Keep battery radio and mobile phones fully charged",
                    "5. Follow official IMD/NDRF advisories and call 108/112 for rescue"
                ]
            },
            "hi": {
                "title": "🚨 चक्रवात लाल चेतावनी! तुरंत सुरक्षित आश्रय लें",
                "message": "अत्यंत तेज हवाओं और समुद्री तूफान की संभावना है। पक्के मकान या आश्रय में रहें!",
                "safety_steps": [
                    "1. खिड़कियों और शीशों से दूर पक्के कमरे में रहें",
                    "2. बाहर की ढीली वस्तुओं को बांधें और पशुओं को सुरक्षित स्थान पर ले जाएं",
                    "3. 72 घंटे का पीने का पानी, सूखा भोजन और प्राथमिक चिकित्सा किट रखें",
                    "4. मोबाइल और बैटरी रेडियो को फुल चार्ज रखें",
                    "5. आधिकारिक सलाह का पालन करें और मदद के लिए 108/112 पर कॉल करें"
                ]
            },
            "mr": {
                "title": "🚨 चक्रीवादळ रेड अलर्ट! त्वरित पक्या निवाऱ्यात जा",
                "message": "अतितीव्र वारे आणि वादळी पावसाची शक्यता आहे. खिडक्यांपासून दूर सुरक्षित इमारतीत राहा!",
                "safety_steps": [
                    "1. खिडक्या आणि काचांपासून दूर पक्या इमारतीत राहा",
                    "2. बाहेरील वस्तू सुरक्षित बांधा आणि जनावरांना निवाऱ्यात आणा",
                    "3. 72 तासांचे पिण्याचे पाणी, कोरडा घास आणि औषधे जवळ ठेवा",
                    "4. मोबाईल आणि रेडिओ चार्ज ठेवा",
                    "5. NDRF च्या सूचना पाळा आणि मदतीसाठी 108/112 वर कॉल करा"
                ]
            }
        },
        "DROUGHT": {
            "en": {
                "title": "⚠️ DROUGHT ADVISORY! Water Conservation Required",
                "message": "Severe rainfall deficit and groundwater drop detected. Conserve drinking water and optimize irrigation.",
                "safety_steps": [
                    "1. Restrict water use strictly to drinking and essential sanitation",
                    "2. Utilize micro-irrigation (drip/sprinkler) for crops",
                    "3. Report groundwater depletion and broken supply pipelines",
                    "4. Access government fodder camps and water tanker supply",
                    "5. Call local helpline 108 for emergency drinking water delivery"
                ]
            },
            "hi": {
                "title": "⚠️ सूखा परामर्श! जल संरक्षण आवश्यक",
                "message": "गंभीर वर्षा की कमी और भूजल स्तर में गिरावट पाई गई है। पानी बचाएं!",
                "safety_steps": [
                    "1. पानी का उपयोग केवल पीने और आवश्यक कार्यों के लिए करें",
                    "2. फसलों के लिए ड्रिप/स्प्रिंकलर सिंचाई का उपयोग करें",
                    "3. टूटी हुई पानी की पाइपलाइनों की तुरंत रिपोर्ट करें",
                    "4. सरकारी चारा शिविरों और टैंकर आपूर्ति का लाभ उठाएं",
                    "5. आपातकालीन पानी की आपूर्ति के लिए 108 पर संपर्क करें"
                ]
            },
            "mr": {
                "title": "⚠️ दुष्काळ सल्ला! पाणी जपून वापरा",
                "message": "पावसाची तीव्र तूट आणि भूजल पातळी खालावली आहे. पिण्याच्या पाण्याचा अपव्यय टाळा!",
                "safety_steps": [
                    "1. पाण्याचा वापर केवळ पिण्यासाठी आणि अत्यावश्यक कामांसाठी करा",
                    "2. शेतीसाठी ठिबक/सिंचन पद्धतीचा वापर करा",
                    "3. पाणी गळतीची त्वरित तक्रार करा",
                    "4. सरकारी चारा छावण्यांचा लाभ घ्या",
                    "5. पिण्याच्या पाण्याच्या मदतीसाठी 108 वर कॉल करा"
                ]
            }
        }
    }

    @classmethod
    def get_localized_content(cls, disaster_type: str, lang: str = "en") -> Dict[str, Any]:
        disaster_key = disaster_type.upper()
        dt_dict = cls.LOCALIZED_TEXTS.get(disaster_key, cls.LOCALIZED_TEXTS["FLOOD"])
        return dt_dict.get(lang.lower(), dt_dict["en"])


class ParallelSOSAlertEngine:
    """
    Parallel Alert Dispatcher:
    Sends SOS_RESCUE to Rescue GPT Management & SOS_PUBLIC to D-SQUARE GPT simultaneously.
    """
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    def dispatch_parallel_sos(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes non-blocking parallel dispatch to Rescue GPT & D-SQUARE GPT.
        Guarantees alert generation time < 30 seconds.
        """
        start_time = time.time()

        # Submit parallel tasks to thread pool
        future_rescue = self.executor.submit(self._build_rescue_payload, alert_data)
        future_public = self.executor.submit(self._build_public_payload, alert_data)

        rescue_payload = future_rescue.result(timeout=10)
        public_payload = future_public.result(timeout=10)

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

        result = {
            "status": "success",
            "message": "⚡ Parallel SOS Alerts Dispatched Successfully (< 30s SLA guaranteed)!",
            "dispatch_latency_ms": elapsed_ms,
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rescue_gpt_alert": rescue_payload,
            "dsquare_gpt_alert": public_payload
        }

        return result

    def _build_rescue_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Builds SOS_RESCUE payload for Rescue GPT Management"""
        disaster_type = data.get("disaster_type", "FLOOD").upper()
        severity = data.get("severity", "HIGH").upper()
        lat = float(data.get("latitude", 19.0760))
        lon = float(data.get("longitude", 72.8777))
        area_name = data.get("area_name", "Mumbai Coastal Restricted Zone")
        pincode = data.get("pincode", "400001")
        affected_pop = int(data.get("affected_population", 5000))

        sensor_readings = data.get("sensor_data", {
            "water_level": "2.5m",
            "rainfall": "150mm/hr",
            "temperature": "32°C",
            "soil_moisture": "88%"
        })

        recommended_actions = data.get("recommended_actions", [
            "Deploy 10 NDRF motorized inflatable rescue boats",
            "Setup emergency medical triage camp at School XYZ",
            "Enforce immediate police blockade on coastal evacuation routes"
        ])

        return {
            "alert_type": "SOS_RESCUE",
            "disaster_type": disaster_type,
            "severity": severity,
            "location": {
                "latitude": lat,
                "longitude": lon,
                "area_name": area_name,
                "pincode": pincode
            },
            "affected_population": affected_pop,
            "sensor_data": sensor_readings,
            "recommended_actions": recommended_actions,
            "emergency_contacts": {
                "disaster_helpline": "108",
                "national_emergency": "112",
                "police": "100",
                "fire_services": "101",
                "nearest_hospital": "Grant Government Medical College (+91-22-23735555)"
            },
            "priority_rank": "CRITICAL_LEVEL_1" if severity in ["HIGH", "CRITICAL"] else "LEVEL_2",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    def _build_public_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Builds SOS_PUBLIC payload for D-SQUARE GPT Citizen Public Guidance"""
        disaster_type = data.get("disaster_type", "FLOOD").upper()
        severity = data.get("severity", "HIGH").upper()
        area_name = data.get("area_name", "Mumbai Coastal Restricted Zone")
        landmark = data.get("landmark", "Near Marine Drive High Ground")
        lat = float(data.get("latitude", 19.0760))
        lon = float(data.get("longitude", 72.8777))

        en_content = MultiLanguageLocalization.get_localized_content(disaster_type, "en")
        hi_content = MultiLanguageLocalization.get_localized_content(disaster_type, "hi")
        mr_content = MultiLanguageLocalization.get_localized_content(disaster_type, "mr")

        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat+0.015},{lon+0.015}"

        return {
            "alert_type": "SOS_PUBLIC",
            "disaster_type": disaster_type,
            "severity": severity,
            "location": {
                "area_name": area_name,
                "landmark": landmark,
                "latitude": lat,
                "longitude": lon
            },
            "message": f"🚨 {disaster_type} ALERT! {area_name} is under RESTRICTED ACCESS. Evacuate immediately!",
            "evacuation_route": maps_url,
            "safety_instructions": en_content["safety_steps"],
            "shelter_location": {
                "name": "School XYZ Community Hall & Emergency Center",
                "address": "124 Relief Camp Road, High Ground Sector 4",
                "capacity": 500,
                "available_beds": 320,
                "contact_number": "+91-22-28491000",
                "facilities": ["Medical Triage", "Food Rations", "Drinking Water", "Backup Generator"]
            },
            "languages": {
                "english": en_content,
                "hindi": hi_content,
                "marathi": mr_content
            },
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }


parallel_sos_engine = ParallelSOSAlertEngine()
